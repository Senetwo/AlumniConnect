from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.datastructures import Headers

from app.core import clerk_auth


def request_with_token(token="signed-session"):
    return SimpleNamespace(headers=Headers({"Authorization": f"Bearer {token}"}))


def test_clerk_request_returns_verified_subject(monkeypatch):
    monkeypatch.setattr(clerk_auth.settings, "clerk_secret_key", "sk_test_placeholder")
    state = SimpleNamespace(is_signed_in=True, payload={"sub": "user_clerk_123"})
    monkeypatch.setattr(clerk_auth, "authenticate_request", lambda request, options: state)

    assert clerk_auth.verify_clerk_request(request_with_token())["sub"] == "user_clerk_123"


def test_invalid_or_expired_clerk_token_is_rejected(monkeypatch):
    monkeypatch.setattr(clerk_auth.settings, "clerk_secret_key", "sk_test_placeholder")
    monkeypatch.setattr(clerk_auth, "authenticate_request", lambda request, options: (_ for _ in ()).throw(ValueError("invalid signature")))

    with pytest.raises(HTTPException) as error:
        clerk_auth.verify_clerk_request(request_with_token("expired-or-invalid"))

    assert error.value.status_code == 401


def test_signed_out_clerk_state_is_rejected(monkeypatch):
    monkeypatch.setattr(clerk_auth.settings, "clerk_secret_key", "sk_test_placeholder")
    state = SimpleNamespace(is_signed_in=False, payload=None, status="signed-out", reason="test", message="signed out")
    monkeypatch.setattr(clerk_auth, "authenticate_request", lambda request, options: state)

    with pytest.raises(HTTPException) as error:
        clerk_auth.verify_clerk_request(request_with_token())

    assert error.value.status_code == 401


def test_missing_clerk_configuration_fails_closed(monkeypatch):
    monkeypatch.setattr(clerk_auth.settings, "clerk_secret_key", "")

    with pytest.raises(HTTPException) as error:
        clerk_auth.verify_clerk_request(request_with_token())

    assert error.value.status_code == 503
