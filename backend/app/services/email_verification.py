from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import hashlib
import hmac
import logging
import secrets
import smtplib
import ssl

from sqlalchemy.orm import Session

from app.database.database import settings
from app.models.email_verification import EmailVerificationToken
from app.models.login_challenge import LoginChallenge
from app.models.password_reset import PasswordResetToken
from app.models.user import User


LOGIN_CODE_LIFETIME = timedelta(minutes=10)
LOGIN_CODE_MAX_ATTEMPTS = 5
LOGIN_CODE_RESEND_COOLDOWN = timedelta(seconds=30)
TOKEN_LIFETIME = timedelta(hours=24)
PASSWORD_RESET_LIFETIME = timedelta(hours=1)
logger = logging.getLogger(__name__)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def code_digest(code: str) -> str:
    # Keyed, so a leaked table cannot be brute-forced offline without the secret.
    return hmac.new(settings.secret_key.encode("utf-8"), code.encode("utf-8"), hashlib.sha256).hexdigest()


def issue_login_challenge(db: Session, user: User) -> tuple[str, str]:
    """Create a fresh challenge for the user and return (challenge_token, code)."""
    challenge_token = secrets.token_urlsafe(32)
    code = f"{secrets.randbelow(1_000_000):06d}"
    db.query(LoginChallenge).filter(LoginChallenge.user_id == user.id).delete(synchronize_session=False)
    db.add(LoginChallenge(
        user_id=user.id,
        challenge_hash=token_digest(challenge_token),
        code_hash=code_digest(code),
        expires_at=datetime.now(timezone.utc) + LOGIN_CODE_LIFETIME,
    ))
    return challenge_token, code


def rotate_login_code(challenge: LoginChallenge) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    now = datetime.now(timezone.utc)
    challenge.code_hash = code_digest(code)
    challenge.attempts = 0
    challenge.last_sent_at = now
    challenge.expires_at = now + LOGIN_CODE_LIFETIME
    return code


def display_email(email: str) -> str:
    """Drop a Gmail plus-address prefix (owner+tag@x -> tag@x) so the owner's address is not shown."""
    local, _, domain = email.partition("@")
    plus = local.find("+")
    return f"{local[plus + 1:]}@{domain}" if domain and plus > 0 else email


def mask_email(email: str) -> str:
    local, _, domain = display_email(email).partition("@")
    return f"{local[:1]}{'*' * min(max(len(local) - 1, 2), 6)}@{domain}"


def issue_verification_token(db: Session, user: User) -> str:
    raw_token = secrets.token_urlsafe(40)
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id
    ).delete(synchronize_session=False)
    db.add(EmailVerificationToken(
        user_id=user.id,
        token_hash=token_digest(raw_token),
        expires_at=datetime.now(timezone.utc) + TOKEN_LIFETIME,
    ))
    return raw_token


def issue_password_reset_token(db: Session, user: User) -> str:
    raw_token = secrets.token_urlsafe(40)
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id
    ).delete(synchronize_session=False)
    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=token_digest(raw_token),
        expires_at=datetime.now(timezone.utc) + PASSWORD_RESET_LIFETIME,
    ))
    return raw_token


def send_login_code_email(email: str, full_name: str, code: str) -> bool:
    if not all((settings.smtp_host, settings.smtp_from_email)):
        raise RuntimeError("Email delivery is not configured")

    message = EmailMessage()
    message["Subject"] = "Your AlumniConnect sign-in code"
    message["From"] = settings.smtp_from_email
    message["To"] = email
    message.set_content(
        f"Hello {full_name},\n\n"
        f"Your AlumniConnect sign-in code is {code}. It expires in 10 minutes.\n\n"
        "If you did not try to sign in, ignore this email and consider changing your password."
    )
    return _send_or_log_development(message, "sign-in code", code)


def send_verification_email(email: str, full_name: str, token: str) -> bool:
    if not all((settings.smtp_host, settings.smtp_from_email)):
        raise RuntimeError("Email delivery is not configured")

    verify_url = f"{settings.frontend_base_url.rstrip('/')}/verify-email?token={token}"
    message = EmailMessage()
    message["Subject"] = "Verify your AlumniConnect email"
    message["From"] = settings.smtp_from_email
    message["To"] = email
    message.set_content(
        f"Hello {full_name},\n\n"
        "Please verify your email address to activate your AlumniConnect account. "
        f"This link expires in 24 hours:\n\n{verify_url}\n\n"
        "If you did not create this account, you can ignore this email."
    )

    return _send_or_log_development(message, "email verification", verify_url)


def send_password_reset_email(email: str, full_name: str, token: str) -> bool:
    if not all((settings.smtp_host, settings.smtp_from_email)):
        raise RuntimeError("Email delivery is not configured")

    reset_url = f"{settings.frontend_base_url.rstrip('/')}/reset-password?token={token}"
    message = EmailMessage()
    message["Subject"] = "Reset your AlumniConnect password"
    message["From"] = settings.smtp_from_email
    message["To"] = email
    message.set_content(
        f"Hello {full_name},\n\n"
        "A password reset was requested for your AlumniConnect account. "
        f"Use this link within one hour to set a new password:\n\n{reset_url}\n\n"
        "If you did not request this change, you can ignore this email."
    )

    return _send_or_log_development(message, "password reset", reset_url)


def _send_or_log_development(message: EmailMessage, purpose: str, link: str) -> bool:
    try:
        _send_message(message)
        return True
    except Exception:
        if settings.app_env.casefold() != "development" or not settings.email_dev_fallback:
            raise
        logger.warning(
            "SMTP delivery failed. Local development %s link (one-time, expires soon): %s",
            purpose,
            link,
        )
        return False


def _send_message(message: EmailMessage) -> None:
    if not all((settings.smtp_host, settings.smtp_from_email)):
        raise RuntimeError("Email delivery is not configured")

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, context=ssl.create_default_context()) as smtp:
            _deliver(smtp, message)
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            if settings.smtp_use_starttls:
                smtp.starttls(context=ssl.create_default_context())
            _deliver(smtp, message)


def _deliver(smtp, message: EmailMessage) -> None:
    if settings.smtp_username:
        smtp.login(settings.smtp_username, settings.smtp_password)
    smtp.send_message(message)
