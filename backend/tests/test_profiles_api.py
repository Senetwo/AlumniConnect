
def register_user(client, email, role):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": f"Test {role.title()}",
            "email": email,
            "password": "TestPassword123!",
            "role": role,
            "profile": {
                "career_domain": "Technology & Digital",
                "career_path": "Software Engineering",
                "experience": "5 years" if role == "mentor" else "Student",
                "skills": ["Python", "FastAPI"],
                "certifications": [],
                "career_goals": "Build impactful software",
                "mentorship_interests": ["Backend development"],
                "availability": "Weekends",
                "bio": "Test profile",
            },
        },
    )
    assert response.status_code in (200, 201), response.text

    
    login = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )
    assert login.status_code == 200, login.text

    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}



def test_get_my_profile(client):
    headers = register_user(client, "profile@example.com", "mentee")

    response = client.get("/api/profiles/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["career_domain"] == "Technology & Digital"
    assert data["skills"] == ["Python", "FastAPI"]


def test_update_my_profile(client):
    headers = register_user(client, "update@example.com", "mentee")

    updated_profile = {
        "user_id": 1,
        "career_domain": "Commercial & Corporate",
        "career_path": "Product Management",
        "experience": "Early career",
        "skills": ["Communication", "Product Strategy"],
        "certifications": ["Scrum"],
        "career_goals": "Become a product leader",
        "mentorship_interests": ["Leadership"],
        "availability": "Evenings",
        "bio": "Updated test profile",
    }

    response = client.patch(
        "/api/profiles/me",
        headers=headers,
        json=updated_profile,
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["career_path"] == "Product Management"
    assert data["skills"] == ["Communication", "Product Strategy"]
    assert data["bio"] == "Updated test profile"


def test_get_my_profile_requires_authentication(client):
    response = client.get("/api/profiles/me")
    assert response.status_code == 401


def test_update_my_profile_requires_authentication(client):
    response = client.patch(
        "/api/profiles/me",
        json={},
    )
    assert response.status_code == 401
