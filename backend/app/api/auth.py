from datetime import datetime, timezone
import hmac
import secrets
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.user import User
from app.models.profile import Profile
from app.schemas.auth import UserLogin, UserRegister, Token, LoginResponse, OtpVerifyRequest, OtpResendRequest, UserResponse, ClerkOnboarding, EmailVerificationRequest, EmailAddressRequest, PasswordResetRequest
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.database.database import settings
from app.models.email_verification import EmailVerificationToken
from app.models.password_reset import PasswordResetToken
from app.models.login_challenge import LoginChallenge
from app.services.email_verification import (
    issue_verification_token,
    issue_password_reset_token,
    issue_login_challenge,
    rotate_login_code,
    code_digest,
    mask_email,
    send_login_code_email,
    LOGIN_CODE_MAX_ATTEMPTS,
    LOGIN_CODE_RESEND_COOLDOWN,
    send_verification_email,
    send_password_reset_email,
    token_digest,
)
from app.ml.mentor_index_service import mentor_index_service
from app.core.clerk_auth import verify_clerk_request, verify_clerk_token, get_clerk_user, verified_primary_email
from fastapi import Request

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def find_user_by_login_email(db: Session, email: str):
    """Exact (case-insensitive) match first; with plus_alias_login, also accept the clean
    tag@domain form of a stored owner+tag@domain address. Only unambiguous matches resolve."""
    wanted = email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == wanted).first()
    if user or not settings.plus_alias_login or "@" not in wanted:
        return user
    local, _, domain = wanted.partition("@")
    matches = db.query(User).filter(func.lower(User.email).like(f"%+{local}@{domain}")).limit(2).all()
    return matches[0] if len(matches) == 1 else None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _clerk_user_response(user: User):
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "community_role": user.community_role,
        "is_email_verified": user.is_email_verified,
    }


@router.get("/clerk/session")
def clerk_session(request: Request, db: Session = Depends(get_db)):
    claims = verify_clerk_request(request)
    clerk_id = claims["sub"]
    user = db.query(User).filter(User.clerk_user_id == clerk_id).first()
    if user is None:
        # Link a legacy account only when Clerk confirms the same verified
        # primary email. Never overwrite an identity already linked elsewhere.
        identity = get_clerk_user(clerk_id)
        email = verified_primary_email(identity)
        if email:
            user = db.query(User).filter(func.lower(User.email) == email.strip().lower()).first()
            if user and user.clerk_user_id and user.clerk_user_id != clerk_id:
                raise HTTPException(status_code=409, detail="This account is linked to a different Clerk identity")
            if user:
                user.clerk_user_id = clerk_id
                try:
                    db.commit()
                except IntegrityError as exc:
                    db.rollback()
                    raise HTTPException(status_code=409, detail="This Clerk identity is already linked to another account") from exc
                db.refresh(user)
    if user is None:
        raise HTTPException(status_code=404, detail="Complete AlumniConnect account setup")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is suspended")
    return _clerk_user_response(user)


@router.post("/clerk/onboard", status_code=status.HTTP_201_CREATED)
def clerk_onboard(data: ClerkOnboarding, request: Request, db: Session = Depends(get_db)):
    claims = verify_clerk_request(request)
    clerk_id = claims["sub"]
    existing = db.query(User).filter(User.clerk_user_id == clerk_id).first()
    if existing:
        return _clerk_user_response(existing)

    identity = get_clerk_user(clerk_id)
    email = verified_primary_email(identity)
    if not email:
        raise HTTPException(status_code=403, detail="Verify a primary email address with Clerk before continuing")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=409,
            detail="An AlumniConnect account already uses this email. Sign in to that account and link Clerk explicitly; accounts are never merged by email alone.",
        )

    profile_data = data.profile
    user = User(
        full_name=data.full_name.strip(),
        email=email,
        password_hash=hash_password(secrets.token_urlsafe(32)),
        role=data.role,
        community_role=data.role,
        clerk_user_id=clerk_id,
        is_email_verified=True,
    )
    db.add(user)
    db.flush()
    db.add(Profile(
        user_id=user.id,
        career_domain=profile_data.career_domain,
        career_path=profile_data.career_path,
        experience=profile_data.experience,
        skills=", ".join(profile_data.skills),
        certifications=", ".join(profile_data.certifications),
        career_goals=profile_data.career_goals,
        mentorship_interests=", ".join(profile_data.mentorship_interests),
        availability=profile_data.availability,
        bio=profile_data.bio,
    ))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(User).filter(User.clerk_user_id == clerk_id).first()
        if existing:
            return _clerk_user_response(existing)
        raise HTTPException(status_code=409, detail="This email is already registered")
    db.refresh(user)
    created_profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    if created_profile:
        mentor_index_service.sync_profile(created_profile, user)
    return _clerk_user_response(user)


@router.post("/clerk/link")
def link_clerk_identity(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Linking requires proof of control of both the existing AlumniConnect account
    # (Authorization bearer token) and the Clerk account (second bearer token).
    raw_token = request.headers.get("x-clerk-authorization", "")
    scheme, _, clerk_token = raw_token.partition(" ")
    if scheme.lower() != "bearer" or not clerk_token:
        raise HTTPException(status_code=401, detail="A Clerk session token is required to link accounts")
    claims = verify_clerk_token(clerk_token)
    clerk_id = claims["sub"]
    if current_user.clerk_user_id and current_user.clerk_user_id != clerk_id:
        raise HTTPException(status_code=409, detail="This AlumniConnect account is already linked to another Clerk identity")
    other_user = db.query(User).filter(User.clerk_user_id == clerk_id).first()
    if other_user and other_user.id != current_user.id:
        raise HTTPException(status_code=409, detail="This Clerk identity is already linked to another AlumniConnect account")
    current_user.clerk_user_id = clerk_id
    db.commit()
    return _clerk_user_response(current_user)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        func.lower(User.email) == user_data.email.strip().lower()
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        community_role=user_data.role,
        is_email_verified=not settings.email_verification_required or settings.app_env == "test",
    )

    db.add(user)
    db.flush()

    profile = Profile(
        user_id=user.id,
        career_domain=user_data.profile.career_domain,
        career_path=user_data.profile.career_path,
        experience=user_data.profile.experience,
        skills=", ".join(user_data.profile.skills),
        certifications=", ".join(user_data.profile.certifications),
        career_goals=user_data.profile.career_goals,
        mentorship_interests=", ".join(
            user_data.profile.mentorship_interests
        ),
        availability=user_data.profile.availability,
        bio=user_data.profile.bio
    )

    db.add(profile)
    db.commit()
    db.refresh(user)
    mentor_index_service.sync_profile(profile, user)

    if settings.email_verification_required and settings.app_env != "test":
        token = issue_verification_token(db, user)
        db.commit()
        try:
            email_sent = send_verification_email(user.email, user.full_name, token)
        except Exception as exc:
            # Keep the token so the user can request another message; never log
            # the token or SMTP credentials.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Account created, but verification email could not be sent. Use resend verification after email delivery is configured.",
            ) from exc

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "is_email_verified": user.is_email_verified,
        "verification_email_sent": email_sent if settings.email_verification_required and settings.app_env != "test" else None,
    }


@router.post("/login", response_model=LoginResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = find_user_by_login_email(db, user_data.email)

    if not user or not verify_password(
        user_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is suspended. Contact support.")

    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before signing in. You can request a new verification email.",
        )

    if settings.login_otp_required and settings.app_env != "test":
        challenge_token, code = issue_login_challenge(db, user)
        db.commit()
        try:
            email_sent = send_login_code_email(user.email, user.full_name, code)
        except Exception as exc:
            db.query(LoginChallenge).filter(LoginChallenge.user_id == user.id).delete(synchronize_session=False)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="We could not send your sign-in code. Please try again shortly.",
            ) from exc
        return {
            "mfa_required": True,
            "challenge_token": challenge_token,
            "email_hint": mask_email(user.email),
            "email_sent": email_sent,
        }

    return _session_token(user)


def _session_token(user: User) -> dict:
    return {
        "access_token": create_access_token({"sub": str(user.id), "role": user.role}),
        "token_type": "bearer",
    }


def _find_challenge(db: Session, challenge_token: str) -> LoginChallenge:
    challenge = db.query(LoginChallenge).filter(
        LoginChallenge.challenge_hash == token_digest(challenge_token)
    ).first()
    invalid = HTTPException(status_code=400, detail="This sign-in request has expired. Sign in again.")
    if not challenge:
        raise invalid
    expiry = challenge.expires_at
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if expiry <= datetime.now(timezone.utc):
        db.delete(challenge)
        db.commit()
        raise invalid
    return challenge


@router.post("/login/verify-otp", response_model=Token)
def verify_login_code(payload: OtpVerifyRequest, db: Session = Depends(get_db)):
    challenge = _find_challenge(db, payload.challenge_token)

    if not hmac.compare_digest(challenge.code_hash, code_digest(payload.code)):
        challenge.attempts += 1
        remaining = LOGIN_CODE_MAX_ATTEMPTS - challenge.attempts
        if remaining <= 0:
            db.delete(challenge)
            db.commit()
            raise HTTPException(status_code=400, detail="Too many incorrect codes. Sign in again to get a new one.")
        db.commit()
        raise HTTPException(
            status_code=400,
            detail=f"That code is not correct. {remaining} attempt{'s' if remaining != 1 else ''} left.",
        )

    user = db.query(User).filter(User.id == challenge.user_id).first()
    db.delete(challenge)
    db.commit()
    if not user or not user.is_active or not user.is_email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account cannot sign in.")
    return _session_token(user)


@router.post("/login/resend-otp")
def resend_login_code(payload: OtpResendRequest, db: Session = Depends(get_db)):
    challenge = _find_challenge(db, payload.challenge_token)
    sent_at = challenge.last_sent_at
    if sent_at.tzinfo is None:
        sent_at = sent_at.replace(tzinfo=timezone.utc)
    wait = LOGIN_CODE_RESEND_COOLDOWN - (datetime.now(timezone.utc) - sent_at)
    if wait.total_seconds() > 0:
        raise HTTPException(
            status_code=429,
            detail=f"Please wait {int(wait.total_seconds()) + 1} seconds before requesting another code.",
        )
    user = db.query(User).filter(User.id == challenge.user_id).first()
    code = rotate_login_code(challenge)
    db.commit()
    try:
        email_sent = send_login_code_email(user.email, user.full_name, code)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="We could not send your sign-in code. Please try again shortly.") from exc
    return {"message": "A new code was sent.", "email_sent": email_sent}


@router.post("/verify-email")
def verify_email(payload: EmailVerificationRequest, db: Session = Depends(get_db)):
    verification = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token_hash == token_digest(payload.token)
    ).first()
    if not verification:
        raise HTTPException(status_code=400, detail="This verification link is invalid or has already been used.")

    expiry = verification.expires_at
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if expiry <= datetime.now(timezone.utc):
        db.delete(verification)
        db.commit()
        raise HTTPException(status_code=400, detail="This verification link has expired. Request a new one.")

    user = db.query(User).filter(User.id == verification.user_id).first()
    if not user:
        db.delete(verification)
        db.commit()
        raise HTTPException(status_code=400, detail="This verification link is invalid or has already been used.")

    user.is_email_verified = True
    db.delete(verification)
    db.commit()
    return {"message": "Email verified. You can now sign in."}


@router.post("/resend-verification")
def resend_verification(payload: EmailAddressRequest, db: Session = Depends(get_db)):
    user = find_user_by_login_email(db, payload.email)
    if user and not user.is_email_verified:
        token = issue_verification_token(db, user)
        db.commit()
        try:
            email_sent = send_verification_email(user.email, user.full_name, token)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Email delivery is unavailable. Please try again later.") from exc
    else:
        email_sent = True
    return {
        "message": "If this account needs verification, a link was sent by email or logged in the backend terminal for local development.",
        "email_sent": email_sent,
    }


@router.post("/password-reset/request")
def request_password_reset(payload: EmailAddressRequest, db: Session = Depends(get_db)):
    user = find_user_by_login_email(db, payload.email)
    if user:
        token = issue_password_reset_token(db, user)
        db.commit()
        try:
            email_sent = send_password_reset_email(user.email, user.full_name, token)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Password reset email could not be sent. Check email delivery settings and try again.",
            ) from exc
    else:
        email_sent = True
    return {
        "message": "If an account exists for that email, a reset link was sent by email or logged in the backend terminal for local development.",
        "email_sent": email_sent,
    }


@router.post("/password-reset/confirm")
def confirm_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    reset = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_digest(payload.token)
    ).first()
    if not reset:
        raise HTTPException(status_code=400, detail="This password reset link is invalid or has already been used.")

    expiry = reset.expires_at
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if expiry <= datetime.now(timezone.utc):
        db.delete(reset)
        db.commit()
        raise HTTPException(status_code=400, detail="This password reset link has expired. Request a new one.")

    user = db.query(User).filter(User.id == reset.user_id).first()
    if not user:
        db.delete(reset)
        db.commit()
        raise HTTPException(status_code=400, detail="This password reset link is invalid or has already been used.")

    user.password_hash = hash_password(payload.new_password)
    # Following a reset link proves control of the account's email address.
    user.is_email_verified = True
    db.delete(reset)
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).delete(synchronize_session=False)
    db.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user.id).delete(synchronize_session=False)
    db.query(LoginChallenge).filter(LoginChallenge.user_id == user.id).delete(synchronize_session=False)
    db.commit()
    return {"message": "Password updated and email verified. You can now sign in."}
    
@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
        "community_role": current_user.community_role or (current_user.role if current_user.role in ("mentor", "mentee") else None),
        "is_active": current_user.is_active
    }
    

