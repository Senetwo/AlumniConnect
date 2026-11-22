from app.models.mentorship import Mentorship
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
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_mentor_and_mentee(client):
    mentee = register_user(
        client, "mentee@example.com", "Test Mentee", "Password123!", "mentee"
    )
    mentor = register_user(
        client, "mentor@example.com", "Test Mentor", "Password123!", "mentor"
    )
    mentee_headers = login_user(client, "mentee@example.com", "Password123!")
    mentor_headers = login_user(client, "mentor@example.com", "Password123!")
    return mentee, mentor, mentee_headers, mentor_headers


def test_create_request_requires_authentication(client):
    response = client.post("/api/mentorships/", json={"mentor_id": 2, "motivation": "I would like guidance on my next career step."})
    assert response.status_code == 401


def test_mentee_can_request_mentorship(client, db):
    _, mentor, mentee_headers, _ = create_mentor_and_mentee(client)

    response = client.post(
        "/api/mentorships/",
        json={"mentor_id": mentor["id"], "motivation": "I would like guidance on my next career step."},
        headers=mentee_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["mentor_id"] == mentor["id"]
    assert data["status"] == "pending"

    saved = db.query(Mentorship).filter_by(id=data["id"]).first()
    assert saved is not None
    assert saved.status == "pending"


def test_duplicate_active_request_is_rejected(client):
    _, mentor, mentee_headers, _ = create_mentor_and_mentee(client)

    first = client.post(
        "/api/mentorships/",
        json={"mentor_id": mentor["id"], "motivation": "I would like guidance on my next career step."},
        headers=mentee_headers,
    )
    second = client.post(
        "/api/mentorships/",
        json={"mentor_id": mentor["id"], "motivation": "I would like guidance on my next career step."},
        headers=mentee_headers,
    )

    assert first.status_code == 201
    assert second.status_code == 409


def test_invalid_mentor_is_rejected(client):
    create_mentor_and_mentee(client)
    mentee_headers = login_user(client, "mentee@example.com", "Password123!")

    response = client.post(
        "/api/mentorships/",
        json={"mentor_id": 99999, "motivation": "I would like guidance on my next career step."},
        headers=mentee_headers,
    )

    assert response.status_code == 404


def test_mentor_can_view_incoming_requests(client):
    mentee, mentor, mentee_headers, mentor_headers = create_mentor_and_mentee(client)

    created = client.post(
        "/api/mentorships/",
        json={"mentor_id": mentor["id"], "motivation": "I would like guidance on my next career step."},
        headers=mentee_headers,
    )
    assert created.status_code == 201

    response = client.get(
        "/api/mentorships/incoming",
        headers=mentor_headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["mentee_id"] == mentee["id"]
    assert response.json()[0]["mentee_name"] == "Test Mentee"
    assert response.json()[0]["mentor_name"] == "Test Mentor"


def test_mentee_outgoing_requests_include_names(client):
    _, mentor, mentee_headers, _ = create_mentor_and_mentee(client)

    client.post(
        "/api/mentorships/",
        json={"mentor_id": mentor["id"], "motivation": "I would like guidance on my next career step."},
        headers=mentee_headers,
    )

    response = client.get("/api/mentorships/outgoing", headers=mentee_headers)

    assert response.status_code == 200
    assert response.json()[0]["mentor_name"] == "Test Mentor"
    assert response.json()[0]["mentee_name"] == "Test Mentee"


def test_mentee_cannot_view_incoming_requests(client):
    create_mentor_and_mentee(client)
    mentee_headers = login_user(client, "mentee@example.com", "Password123!")

    response = client.get(
        "/api/mentorships/incoming",
        headers=mentee_headers,
    )

    assert response.status_code == 403


def test_mentor_can_accept_request(client):
    _, mentor, mentee_headers, mentor_headers = create_mentor_and_mentee(client)

    created = client.post(
        "/api/mentorships/",
        json={"mentor_id": mentor["id"], "motivation": "I would like guidance on my next career step."},
        headers=mentee_headers,
    )
    mentorship_id = created.json()["id"]

    response = client.patch(
        f"/api/mentorships/{mentorship_id}/respond",
        json={"decision": "accepted"},
        headers=mentor_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert response.json()["responded_at"] is not None


def test_mentor_can_decline_request(client):
    _, mentor, mentee_headers, mentor_headers = create_mentor_and_mentee(client)

    created = client.post(
        "/api/mentorships/",
        json={"mentor_id": mentor["id"], "motivation": "I would like guidance on my next career step."},
        headers=mentee_headers,
    )
    mentorship_id = created.json()["id"]

    response = client.patch(
        f"/api/mentorships/{mentorship_id}/respond",
        json={"decision": "declined"},
        headers=mentor_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "declined"


def test_other_mentor_cannot_respond_to_request(client):
    _, mentor, mentee_headers, _ = create_mentor_and_mentee(client)

    register_user(
        client, "othermentor@example.com", "Other Mentor", "Password123!", "mentor"
    )
    other_mentor_headers = login_user(
        client, "othermentor@example.com", "Password123!"
    )

    created = client.post(
        "/api/mentorships/",
        json={"mentor_id": mentor["id"], "motivation": "I would like guidance on my next career step."},
        headers=mentee_headers,
    )
    mentorship_id = created.json()["id"]

    response = client.patch(
        f"/api/mentorships/{mentorship_id}/respond",
        json={"decision": "accepted"},
        headers=other_mentor_headers,
    )

    assert response.status_code == 404


def test_cannot_respond_to_non_pending_request(client):
    _, mentor, mentee_headers, mentor_headers = create_mentor_and_mentee(client)

    created = client.post(
        "/api/mentorships/",
        json={"mentor_id": mentor["id"], "motivation": "I would like guidance on my next career step."},
        headers=mentee_headers,
    )
    mentorship_id = created.json()["id"]

    first = client.patch(
        f"/api/mentorships/{mentorship_id}/respond",
        json={"decision": "accepted"},
        headers=mentor_headers,
    )
    second = client.patch(
        f"/api/mentorships/{mentorship_id}/respond",
        json={"decision": "declined"},
        headers=mentor_headers,
    )

    assert first.status_code == 200
    assert second.status_code == 409
    

def test_declined_request_can_be_submitted_again(client):
    _, mentor, mentee_headers, mentor_headers = create_mentor_and_mentee(client)

    first = client.post(
        "/api/mentorships/",
        json={"mentor_id": mentor["id"], "motivation": "I would like guidance on my next career step."},
        headers=mentee_headers,
    )
    assert first.status_code == 201

    declined = client.patch(
        f"/api/mentorships/{first.json()['id']}/respond",
        json={"decision": "declined"},
        headers=mentor_headers,
    )
    assert declined.status_code == 200
    assert declined.json()["status"] == "declined"

    second = client.post(
        "/api/mentorships/",
        json={"mentor_id": mentor["id"], "motivation": "I would like guidance on my next career step."},
        headers=mentee_headers,
    )

    assert second.status_code == 201
    assert second.json()["status"] == "pending"


def test_mentee_cannot_respond_to_mentorship_request(client):
    _, mentor, mentee_headers, mentor_headers = create_mentor_and_mentee(client)

    created = client.post(
        "/api/mentorships/",
        json={"mentor_id": mentor["id"], "motivation": "I would like guidance on my next career step."},
        headers=mentee_headers,
    )
    assert created.status_code == 201

    response = client.patch(
        f"/api/mentorships/{created.json()['id']}/respond",
        json={"decision": "accepted"},
        headers=mentee_headers,
    )

    assert response.status_code == 403
