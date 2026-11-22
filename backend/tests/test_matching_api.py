from app.models.user import User

def profile_data():
    return {
        "career_domain": "Technology & Digital",
        "career_path": "Software Engineering",
        "experience": "2 years",
        "skills": ["Python", "FastAPI"],
        "certifications": [],
        "career_goals": "Become a software engineer",
        "mentorship_interests": ["Backend Development"],
        "availability": "Weekdays",
        "bio": "Test profile",
    }


def register_user(client, email, full_name, password, role):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": full_name,
            "password": password,
            "role": role,
            "profile": profile_data(),
        },
    )

    assert response.status_code == 201
    return response.json()


def login_user(client, email, password):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }


def test_matching_me_requires_authentication(client):
    response = client.get("/api/matches/me")

    assert response.status_code == 401


def test_matching_by_id_requires_authentication(client):
    response = client.get("/api/matches/1")

    assert response.status_code == 401


def test_matching_by_id_only_allows_current_mentee(client, db):
    register_user(
        client,
        "first-mentee@example.com",
        "First Mentee",
        "Password123!",
        "mentee",
    )
    register_user(
        client,
        "second-mentee@example.com",
        "Second Mentee",
        "Password123!",
        "mentee",
    )

    first_headers = login_user(
        client,
        "first-mentee@example.com",
        "Password123!",
    )
    second_profile_id = (
        db.query(User)
        .filter(User.email == "second-mentee@example.com")
        .first()
        .profile.id
    )

    response = client.get(
        f"/api/matches/{second_profile_id}",
        headers=first_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You can only view your own recommendations"


def test_mentor_profile_requires_authentication(client):
    response = client.get("/api/matches/mentor/1")

    assert response.status_code == 401


def test_mentor_profile_only_exposes_recommended_mentors(
    client,
    db,
    monkeypatch,
):
    register_user(
        client,
        "profile-mentee@example.com",
        "Profile Mentee",
        "Password123!",
        "mentee",
    )
    register_user(
        client,
        "profile-mentor@example.com",
        "Profile Mentor",
        "Password123!",
        "mentor",
    )
    headers = login_user(
        client,
        "profile-mentee@example.com",
        "Password123!",
    )
    mentor_profile_id = (
        db.query(User)
        .filter(User.email == "profile-mentor@example.com")
        .first()
        .profile.id
    )
    monkeypatch.setattr(
        "app.api.matches.matching_service.retrieve_mentor_candidates",
        lambda mentee, n_results=5: [],
    )

    response = client.get(
        f"/api/matches/mentor/{mentor_profile_id}",
        headers=headers,
    )

    assert response.status_code == 404


def test_matching_me_rejects_mentor(client):
    register_user(
        client,
        "mentor@example.com",
        "Test Mentor",
        "Password123!",
        "mentor",
    )

    headers = login_user(
        client,
        "mentor@example.com",
        "Password123!",
    )

    response = client.get(
        "/api/matches/me",
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Only mentees can retrieve mentor recommendations"
    )


def test_matching_me_rejects_admin_registration(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "admin@example.com",
            "full_name": "Test Admin",
            "password": "Password123!",
            "role": "admin",
            "profile": profile_data(),
        },
    )

    assert response.status_code == 422
    
def test_matching_me_returns_ranked_mentor_recommendations(
    client,
    db,
    monkeypatch
):
    register_user(
        client,
        "mentee@example.com",
        "Test Mentee",
        "Password123!",
        "mentee",
    )

    register_user(
        client,
        "mentor@example.com",
        "Test Mentor",
        "Password123!",
        "mentor",
    )

    headers = login_user(
        client,
        "mentee@example.com",
        "Password123!",
    )

    mentee = (
        db.query(User)
        .filter(User.email == "mentee@example.com")
        .first()
    )

    mentor = (
        db.query(User)
        .filter(User.email == "mentor@example.com")
        .first()
    )

    monkeypatch.setattr(
        "app.api.matches.matching_service.retrieve_mentor_candidates",
        lambda mentee, n_results=5: [
            {
                "mentor_id": mentor.profile.id,
                "distance": 0.05,
                "similarity": 0.95,
            }
        ],
    )

    response = client.get(
        "/api/matches/me",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["mentee_id"] == mentee.profile.id
    assert len(data["matches"]) == 1

    match = data["matches"][0]

    assert match["id"] == mentor.profile.id
    assert match["user_id"] == mentor.id
    assert match["full_name"] == "Test Mentor"
    assert match["career_domain"] == "Technology & Digital"
    assert match["career_path"] == "Software Engineering"
    assert match["similarity_score"] == 95.0
