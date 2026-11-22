from datetime import datetime, timedelta, timezone

import pytest

from app.database.database import settings
from app.models.login_challenge import LoginChallenge

EMAIL = "otp-user@test.com"
PASSWORD = "SecurePassword123!"


@pytest.fixture
def otp_client(client, monkeypatch):
    """A client with a registered, verified user and the email step switched on."""
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Otp User",
            "email": EMAIL,
            "password": PASSWORD,
            "role": "mentee",
            "profile": {
                "career_domain": "technology-digital",
                "career_path": "Software Engineering",
                "experience": "0–2 years",
                "skills": ["Python"],
                "certifications": [],
                "career_goals": "Grow as an engineer",
                "mentorship_interests": [],
                "availability": "Flexible",
                "bio": None,
            },
        },
    )
    assert response.status_code == 201

    sent = []

    def fake_send(email, full_name, code):
        sent.append({"email": email, "code": code})
        return True

    monkeypatch.setattr("app.api.auth.send_login_code_email", fake_send)
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "login_otp_required", True)
    client.sent_codes = sent
    return client


def start_login(client, password=PASSWORD):
    return client.post("/api/auth/login", json={"email": EMAIL, "password": password})


def test_password_login_asks_for_a_code_instead_of_issuing_a_token(otp_client):
    response = start_login(otp_client)

    assert response.status_code == 200
    body = response.json()
    assert body["mfa_required"] is True
    assert body["access_token"] is None
    assert body["challenge_token"]
    assert body["email_hint"].endswith("@test.com")
    assert EMAIL not in str(body)
    assert len(otp_client.sent_codes) == 1
    assert len(otp_client.sent_codes[0]["code"]) == 6


def test_correct_code_issues_a_working_token_once(otp_client):
    challenge = start_login(otp_client).json()["challenge_token"]
    code = otp_client.sent_codes[0]["code"]

    verified = otp_client.post("/api/auth/login/verify-otp", json={"challenge_token": challenge, "code": code})
    assert verified.status_code == 200
    token = verified.json()["access_token"]
    me = otp_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == EMAIL

    replay = otp_client.post("/api/auth/login/verify-otp", json={"challenge_token": challenge, "code": code})
    assert replay.status_code == 400


def test_wrong_password_never_creates_a_challenge(otp_client, db):
    response = start_login(otp_client, password="WrongPassword123!")

    assert response.status_code == 401
    assert db.query(LoginChallenge).count() == 0
    assert otp_client.sent_codes == []


def test_wrong_code_counts_down_and_locks_the_challenge(otp_client):
    challenge = start_login(otp_client).json()["challenge_token"]
    real = otp_client.sent_codes[0]["code"]
    wrong = "000000" if real != "000000" else "111111"

    first = otp_client.post("/api/auth/login/verify-otp", json={"challenge_token": challenge, "code": wrong})
    assert first.status_code == 400
    assert "4 attempts left" in first.json()["detail"]

    for _ in range(4):
        last = otp_client.post("/api/auth/login/verify-otp", json={"challenge_token": challenge, "code": wrong})
    assert "Too many" in last.json()["detail"]

    # Even the right code no longer works once the challenge is gone.
    after = otp_client.post("/api/auth/login/verify-otp", json={"challenge_token": challenge, "code": real})
    assert after.status_code == 400


def test_expired_code_is_rejected(otp_client, db):
    challenge = start_login(otp_client).json()["challenge_token"]
    row = db.query(LoginChallenge).first()
    row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()

    response = otp_client.post(
        "/api/auth/login/verify-otp",
        json={"challenge_token": challenge, "code": otp_client.sent_codes[0]["code"]},
    )
    assert response.status_code == 400
    assert "expired" in response.json()["detail"]


def test_resend_has_a_cooldown_and_replaces_the_old_code(otp_client, db):
    challenge = start_login(otp_client).json()["challenge_token"]
    old_code = otp_client.sent_codes[0]["code"]

    too_soon = otp_client.post("/api/auth/login/resend-otp", json={"challenge_token": challenge})
    assert too_soon.status_code == 429

    row = db.query(LoginChallenge).first()
    row.last_sent_at = datetime.now(timezone.utc) - timedelta(seconds=60)
    db.commit()

    resent = otp_client.post("/api/auth/login/resend-otp", json={"challenge_token": challenge})
    assert resent.status_code == 200
    new_code = otp_client.sent_codes[-1]["code"]

    if new_code != old_code:
        stale = otp_client.post("/api/auth/login/verify-otp", json={"challenge_token": challenge, "code": old_code})
        assert stale.status_code == 400
    fresh = otp_client.post("/api/auth/login/verify-otp", json={"challenge_token": challenge, "code": new_code})
    assert fresh.status_code == 200


def test_malformed_codes_are_rejected_before_any_lookup(otp_client):
    challenge = start_login(otp_client).json()["challenge_token"]

    for bad in ("12345", "abcdef", "1234567"):
        response = otp_client.post("/api/auth/login/verify-otp", json={"challenge_token": challenge, "code": bad})
        assert response.status_code == 422


def test_step_can_be_switched_off_by_configuration(otp_client, monkeypatch):
    monkeypatch.setattr(settings, "login_otp_required", False)

    response = start_login(otp_client)

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["mfa_required"] is False


def test_email_is_matched_regardless_of_letter_case(otp_client):
    response = otp_client.post("/api/auth/login", json={"email": EMAIL.upper(), "password": PASSWORD})

    assert response.status_code == 200
    assert response.json()["mfa_required"] is True
