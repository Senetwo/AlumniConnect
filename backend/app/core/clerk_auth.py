import logging

from fastapi import HTTPException, Request, status
from clerk_backend_api import AuthenticateRequestOptions, authenticate_request

from app.database.database import settings

logger = logging.getLogger(__name__)


def verify_clerk_request(request: Request) -> dict:
    """Verify a Clerk session token and return its signed claims."""
    if not settings.clerk_secret_key:
        raise HTTPException(status_code=503, detail="Clerk authentication is not configured")
    options = AuthenticateRequestOptions(
        secret_key=settings.clerk_secret_key,
        jwt_key=settings.clerk_jwt_key or None,
        authorized_parties=[
            party.strip()
            for party in settings.clerk_authorized_parties.split(",")
            if party.strip()
        ],
        accepts_token=["session_token"],
    )
    try:
        state = authenticate_request(request, options)
    except Exception as exc:
        logger.warning("Clerk session verification raised %r", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Clerk session",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    if not state.is_signed_in or not state.payload or not state.payload.get("sub"):
        logger.warning(
            "Clerk session rejected: status=%s reason=%s message=%s",
            state.status, state.reason, state.message,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Clerk session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return state.payload


def verify_clerk_token(token: str) -> dict:
    from starlette.datastructures import Headers
    from types import SimpleNamespace

    request = SimpleNamespace(headers=Headers({"Authorization": f"Bearer {token}"}))
    return verify_clerk_request(request)


def get_clerk_user(clerk_user_id: str) -> dict:
    """Read verified identity attributes from Clerk's Backend API."""
    if not settings.clerk_secret_key:
        raise HTTPException(status_code=503, detail="Clerk authentication is not configured")
    from urllib.error import HTTPError, URLError
    from urllib.request import Request as URLRequest, urlopen
    import json

    request = URLRequest(
        f"https://api.clerk.com/v1/users/{clerk_user_id}",
        # Clerk's edge (Cloudflare) rejects urllib's default User-Agent with a 403.
        headers={
            "Authorization": f"Bearer {settings.clerk_secret_key}",
            "Accept": "application/json",
            "User-Agent": "AlumniConnect-Backend/1.0",
        },
    )
    try:
        with urlopen(request, timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Unable to verify Clerk account details") from exc


def verified_primary_email(clerk_user: dict) -> str | None:
    primary_id = clerk_user.get("primary_email_address_id")
    for address in clerk_user.get("email_addresses", []):
        if address.get("id") == primary_id and address.get("verification", {}).get("status") == "verified":
            return address.get("email_address")
    return None
