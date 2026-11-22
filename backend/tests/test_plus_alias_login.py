from app.database.database import settings
from app.services.email_verification import display_email, mask_email

PASSWORD = "SecurePassword123!"
STORED = "owner+amina.test@gmail.com"


def _register(client):
    response = client.post("/api/auth/register", json={
        "full_name": "Alias User", "email": STORED, "password": PASSWORD, "role": "mentee",
        "profile": {"career_domain": "technology-digital", "career_path": "Software Engineering",
                    "experience": "0–2 years", "skills": ["Python"], "certifications": [],
                    "career_goals": "Grow", "mentorship_interests": [], "availability": "Flexible", "bio": None},
    })
    assert response.status_code == 201


def test_display_and_mask_hide_the_owner_address():
    assert display_email(STORED) == "amina.test@gmail.com"
    assert display_email("plain@gmail.com") == "plain@gmail.com"
    assert "owner" not in mask_email(STORED)


def test_clean_alias_signs_in_only_when_enabled(client, monkeypatch):
    _register(client)
    body = {"email": "amina.test@gmail.com", "password": PASSWORD}
    monkeypatch.setattr(settings, "plus_alias_login", False)
    assert client.post("/api/auth/login", json=body).status_code == 401
    monkeypatch.setattr(settings, "plus_alias_login", True)
    assert client.post("/api/auth/login", json=body).status_code == 200
    # The stored address keeps working.
    assert client.post("/api/auth/login", json={"email": STORED, "password": PASSWORD}).status_code == 200
