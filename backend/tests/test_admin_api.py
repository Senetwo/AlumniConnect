from app.core.security import create_access_token
from app.models.profile import Profile
from app.models.user import User


def auth_headers(user_id, role):
    token = create_access_token({"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


def make_user(db, name, email, role, community_role=None):
    user = User(
        full_name=name,
        email=email,
        password_hash="not-used-in-this-test",
        role=role,
        community_role=community_role,
        is_email_verified=True,
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add(Profile(
        user_id=user.id,
        career_domain="Technology",
        career_path="Engineering",
        experience="5 years",
        skills="Python",
        certifications="",
        career_goals="Grow",
        mentorship_interests="",
        availability="Weekends",
        bio="Test profile",
    ))
    db.commit()
    return user


def test_admin_dashboard_uses_real_counts_and_marks_untracked_metrics(client, db):
    admin = make_user(db, "Admin", "admin@test.example", "admin", "mentor")
    make_user(db, "Member", "member@test.example", "mentee")

    response = client.get("/api/admin/dashboard", headers=auth_headers(admin.id, "admin"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["metrics"]["total_members"] == 2
    assert payload["metrics"]["active_members"] is None
    assert payload["metrics"]["knowledge_engagement"] is None
    assert len(payload["registration_trend"]) == 30


def test_admin_user_management_is_role_protected_and_audited(client, db):
    admin = make_user(db, "Admin", "admin2@test.example", "admin")
    member = make_user(db, "Member", "member2@test.example", "mentee")
    headers = auth_headers(admin.id, "admin")

    response = client.patch(
        f"/api/admin/users/{member.id}/status",
        headers=headers,
        json={"is_active": False},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert "password_hash" not in client.get("/api/admin/users", headers=headers).text

    forbidden = client.get("/api/admin/users", headers=auth_headers(member.id, "mentee"))
    assert forbidden.status_code == 403


def test_admin_cannot_demote_self(client, db):
    admin = make_user(db, "Admin", "admin3@test.example", "admin")
    response = client.patch(
        f"/api/admin/users/{admin.id}/role",
        headers=auth_headers(admin.id, "admin"),
        json={"role": "mentee"},
    )
    assert response.status_code == 409
