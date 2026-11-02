def profile_data():
    return {
        "career_domain": "Technology & Digital",
        "career_path": "Software Engineering",
        "experience": "2 years",
        "skills": ["Python"],
        "certifications": [],
        "career_goals": "Grow as a software engineer",
        "mentorship_interests": ["Backend"],
        "availability": "Weekdays",
        "bio": "Test profile",
    }


def register(client, email, name, role):
    response = client.post("/api/auth/register", json={
        "full_name": name,
        "email": email,
        "password": "SecurePassword123!",
        "role": role,
        "profile": profile_data(),
    })
    assert response.status_code == 201
    return response.json()


def login(client, email):
    response = client.post("/api/auth/login", json={"email": email, "password": "SecurePassword123!"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def accepted_pair(client):
    mentee = register(client, "chat-mentee@example.com", "Taylor Mentee", "mentee")
    mentor = register(client, "chat-mentor@example.com", "Jordan Mentor", "mentor")
    mentee_headers = login(client, "chat-mentee@example.com")
    mentor_headers = login(client, "chat-mentor@example.com")
    request = client.post("/api/mentorships/", headers=mentee_headers, json={
        "mentor_id": mentor["id"],
        "motivation": "I would value guidance on my next career step.",
    })
    assert request.status_code == 201
    decision = client.patch(
        f"/api/mentorships/{request.json()['id']}/respond",
        headers=mentor_headers,
        json={"decision": "accepted"},
    )
    assert decision.status_code == 200
    return mentee, mentor, mentee_headers, mentor_headers, request.json()["id"]


def test_accepted_mentorship_appears_as_one_named_chat(client):
    mentee, mentor, mentee_headers, mentor_headers, mentorship_id = accepted_pair(client)

    mentee_chats = client.get("/api/chat/conversations", headers=mentee_headers)
    mentor_chats = client.get("/api/chat/conversations", headers=mentor_headers)

    assert mentee_chats.status_code == mentor_chats.status_code == 200
    assert len(mentee_chats.json()) == len(mentor_chats.json()) == 1
    chat = mentee_chats.json()[0]
    assert chat["mentorship_id"] == mentorship_id
    assert chat["mentor_name"] == "Jordan Mentor"
    assert chat["mentee_name"] == "Taylor Mentee"
    assert chat["id"] == mentor_chats.json()[0]["id"]


def test_pending_mentorship_does_not_create_a_chat(client):
    mentor = register(client, "pending-mentor@example.com", "Morgan Mentor", "mentor")
    register(client, "pending-mentee@example.com", "Casey Mentee", "mentee")
    mentee_headers = login(client, "pending-mentee@example.com")
    request = client.post("/api/mentorships/", headers=mentee_headers, json={
        "mentor_id": mentor["id"],
        "motivation": "I would like some guidance on my career goals.",
    })
    assert request.status_code == 201

    response = client.get("/api/chat/conversations", headers=mentee_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_messages_persist_between_authorized_participants(client):
    _, _, mentee_headers, mentor_headers, mentorship_id = accepted_pair(client)
    conversation = client.post(f"/api/chat/conversations/{mentorship_id}", headers=mentee_headers)
    conversation_id = conversation.json()["id"]

    sent = client.post(
        f"/api/chat/conversations/{conversation_id}/messages",
        headers=mentee_headers,
        json={"body": "Hello, I am looking forward to learning from you."},
    )
    received = client.get(
        f"/api/chat/conversations/{conversation_id}/messages",
        headers=mentor_headers,
    )

    assert sent.status_code == 201
    assert received.status_code == 200
    assert received.json()[0]["id"] == sent.json()["id"]
    assert received.json()[0]["body"] == sent.json()["body"]


def test_unrelated_user_cannot_read_mentorship_messages(client):
    _, _, mentee_headers, _, mentorship_id = accepted_pair(client)
    conversation_id = client.post(
        f"/api/chat/conversations/{mentorship_id}",
        headers=mentee_headers,
    ).json()["id"]
    register(client, "chat-outsider@example.com", "Alex Outsider", "mentee")
    outsider_headers = login(client, "chat-outsider@example.com")

    response = client.get(
        f"/api/chat/conversations/{conversation_id}/messages",
        headers=outsider_headers,
    )

    assert response.status_code == 403
