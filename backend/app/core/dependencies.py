import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.database import SessionLocal
from app.models.user import User
from app.core.clerk_auth import verify_clerk_request


security = HTTPBearer()


def community_role(user: User) -> str | None:
    return user.community_role or (user.role if user.role in ("mentor", "mentee") else None)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        # Our own token, just out of date. Say so instead of falling through to Clerk.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        payload = None

    if payload is not None:
        user_id = payload.get("sub")
        try:
            user = db.query(User).filter(User.id == int(user_id)).first() if user_id is not None else None
        except (TypeError, ValueError):
            user = None
    else:
        clerk_payload = verify_clerk_request(request)
        user = db.query(User).filter(User.clerk_user_id == clerk_payload["sub"]).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is not linked to AlumniConnect. Complete account setup first.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is suspended")

    return user

def require_role(required_role: str):
    def role_checker(
        current_user: User = Depends(get_current_user)
    ):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        return current_user

    return role_checker
