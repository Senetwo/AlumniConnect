from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import create_access_token, hash_password
from app.models.community import CommunityEvent
from app.models.network import UserBlock
from app.models.user import User


def make_user(db, name, role="mentee"):
    user = User(
        full_name=name,
        email=f"{name.lower().replace(' ', '.')}@test.com",
        password_hash=hash_password("SecurePassword123!"),
        role=role,
        community_role=role if role != "admin" else None,
        is_email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth(user):
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user.id), 'role': user.role})}"}


@pytest.fixture
def people(db):
    return {
        "amina": make_user(db, "Amina Hassan", "mentor"),
        "otieno": make_user(db, "Otieno Odhiambo", "mentee"),
        "admin": make_user(db, "Site Admin", "admin"),
    }


def future(days=3):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


# ------------------------------------------------------------------ posts

def test_member_can_post_and_everyone_sees_it_newest_first(client, people):
    first = client.post("/api/community/posts", json={"body": "First post"}, headers=auth(people["amina"]))
    assert first.status_code == 201
    client.post("/api/community/posts", json={"body": "Second post"}, headers=auth(people["otieno"]))

    feed = client.get("/api/community/posts", headers=auth(people["amina"])).json()

    assert [p["body"] for p in feed["items"]] == ["Second post", "First post"]
    assert feed["items"][0]["author"]["full_name"] == "Otieno Odhiambo"
    assert feed["items"][0]["can_delete"] is False
    assert feed["items"][1]["can_delete"] is True


def test_blank_and_oversized_posts_are_rejected(client, people):
    for body in ("", "   ", "x" * 2001):
        response = client.post("/api/community/posts", json={"body": body}, headers=auth(people["amina"]))
        assert response.status_code == 422


def test_daily_post_limit(client, people):
    for index in range(10):
        assert client.post("/api/community/posts", json={"body": f"post {index}"}, headers=auth(people["amina"])).status_code == 201
    assert client.post("/api/community/posts", json={"body": "one too many"}, headers=auth(people["amina"])).status_code == 429


def test_only_author_or_admin_can_delete(client, people):
    post = client.post("/api/community/posts", json={"body": "Mine"}, headers=auth(people["amina"])).json()

    assert client.delete(f"/api/community/posts/{post['id']}", headers=auth(people["otieno"])).status_code == 403
    assert client.delete(f"/api/community/posts/{post['id']}", headers=auth(people["admin"])).status_code == 204
    assert client.get("/api/community/posts", headers=auth(people["amina"])).json()["items"] == []


def test_like_is_idempotent_and_reversible(client, people):
    post = client.post("/api/community/posts", json={"body": "Like me"}, headers=auth(people["amina"])).json()
    url = f"/api/community/posts/{post['id']}/like"

    assert client.put(url, headers=auth(people["otieno"])).json() == {"like_count": 1, "liked_by_me": True}
    assert client.put(url, headers=auth(people["otieno"])).json()["like_count"] == 1
    assert client.put(url, headers=auth(people["amina"])).json()["like_count"] == 2

    feed = client.get("/api/community/posts", headers=auth(people["otieno"])).json()["items"][0]
    assert feed["like_count"] == 2 and feed["liked_by_me"] is True

    assert client.delete(url, headers=auth(people["otieno"])).json() == {"like_count": 1, "liked_by_me": False}


def test_blocked_members_do_not_see_each_others_posts(client, db, people):
    client.post("/api/community/posts", json={"body": "Amina writes"}, headers=auth(people["amina"]))
    client.post("/api/community/posts", json={"body": "Otieno writes"}, headers=auth(people["otieno"]))
    db.add(UserBlock(blocker_id=people["otieno"].id, blocked_id=people["amina"].id))
    db.commit()

    def bodies(user):
        return [p["body"] for p in client.get("/api/community/posts", headers=auth(user)).json()["items"]]

    assert bodies(people["otieno"]) == ["Otieno writes"]
    assert bodies(people["amina"]) == ["Amina writes"]
    assert client.put("/api/community/posts/1/like", headers=auth(people["otieno"])).status_code == 404


def test_feed_requires_sign_in(client):
    assert client.get("/api/community/posts").status_code in (401, 403)


# ----------------------------------------------------------------- events

def event_payload(**overrides):
    payload = {
        "title": "Alumni networking evening",
        "description": "An evening for alumni and mentors to meet.",
        "location": "Nairobi, Embakasi",
        "starts_at": future(5),
    }
    payload.update(overrides)
    return payload


def test_only_admins_create_events(client, people):
    denied = client.post("/api/admin/community/events", json=event_payload(), headers=auth(people["amina"]))
    assert denied.status_code == 403

    created = client.post("/api/admin/community/events", json=event_payload(), headers=auth(people["admin"]))
    assert created.status_code == 201


def test_event_validation(client, people):
    admin = auth(people["admin"])
    past = client.post("/api/admin/community/events", json=event_payload(starts_at=future(-1)), headers=admin)
    assert past.status_code == 422
    naive = client.post("/api/admin/community/events", json=event_payload(starts_at="2030-01-01T10:00:00"), headers=admin)
    assert naive.status_code == 422
    backwards = client.post("/api/admin/community/events", json=event_payload(ends_at=future(1)), headers=admin)
    assert backwards.status_code == 422
    script_link = client.post("/api/admin/community/events", json=event_payload(link="javascript:alert(1)"), headers=admin)
    assert script_link.status_code == 422


def test_members_rsvp_and_count_updates(client, people):
    event = client.post("/api/admin/community/events", json=event_payload(), headers=auth(people["admin"])).json()
    url = f"/api/community/events/{event['id']}/rsvp"

    assert client.put(url, headers=auth(people["amina"])).json() == {"going_count": 1, "going_by_me": True}
    assert client.put(url, headers=auth(people["amina"])).json()["going_count"] == 1
    assert client.put(url, headers=auth(people["otieno"])).json()["going_count"] == 2

    listed = client.get("/api/community/events", headers=auth(people["amina"])).json()
    assert listed[0]["going_count"] == 2 and listed[0]["going_by_me"] is True

    assert client.delete(url, headers=auth(people["amina"])).json() == {"going_count": 1, "going_by_me": False}


def test_cancelled_events_disappear_and_reject_rsvps(client, people):
    event = client.post("/api/admin/community/events", json=event_payload(), headers=auth(people["admin"])).json()
    assert client.patch(f"/api/admin/community/events/{event['id']}/cancel", headers=auth(people["admin"])).status_code == 200

    assert client.get("/api/community/events", headers=auth(people["amina"])).json() == []
    assert client.put(f"/api/community/events/{event['id']}/rsvp", headers=auth(people["amina"])).status_code == 404


def test_past_events_are_not_listed(client, db, people):
    db.add(CommunityEvent(
        created_by=people["admin"].id, title="Old event", description="Already happened", location="Nairobi",
        starts_at=datetime.now(timezone.utc) - timedelta(days=2),
    ))
    db.commit()

    assert client.get("/api/community/events", headers=auth(people["amina"])).json() == []


# ------------------------------------------------------------------- jobs

def job_payload(**overrides):
    payload = {
        "title": "Graduate Software Engineer",
        "location": "Nairobi",
        "employment_type": "Full-time",
        "description": "Join the digital team building airline systems.",
        "apply_url": "https://careers.example.com/graduate-engineer",
    }
    payload.update(overrides)
    return payload


def test_only_admins_publish_jobs_and_members_can_read_them(client, people):
    assert client.post("/api/admin/community/jobs", json=job_payload(), headers=auth(people["otieno"])).status_code == 403
    created = client.post("/api/admin/community/jobs", json=job_payload(), headers=auth(people["admin"]))
    assert created.status_code == 201
    assert created.json()["company"] == "Kenya Airways"

    jobs = client.get("/api/community/jobs", headers=auth(people["otieno"])).json()
    assert [job["title"] for job in jobs] == ["Graduate Software Engineer"]


def test_job_needs_a_way_to_apply_and_safe_links(client, people):
    admin = auth(people["admin"])
    nothing = client.post("/api/admin/community/jobs", json=job_payload(apply_url=None), headers=admin)
    assert nothing.status_code == 422
    by_email = client.post("/api/admin/community/jobs", json=job_payload(apply_url=None, contact_email="hr@example.com"), headers=admin)
    assert by_email.status_code == 201
    unsafe = client.post("/api/admin/community/jobs", json=job_payload(apply_url="javascript:alert(1)"), headers=admin)
    assert unsafe.status_code == 422
    bad_type = client.post("/api/admin/community/jobs", json=job_payload(employment_type="Volunteer"), headers=admin)
    assert bad_type.status_code == 422


def test_closed_and_expired_jobs_are_hidden(client, people):
    admin = auth(people["admin"])
    closed = client.post("/api/admin/community/jobs", json=job_payload(title="Closed role"), headers=admin).json()
    client.patch(f"/api/admin/community/jobs/{closed['id']}/close", headers=admin)
    client.post("/api/admin/community/jobs", json=job_payload(title="Expired role", closes_at=future(-1)), headers=admin)
    client.post("/api/admin/community/jobs", json=job_payload(title="Open role", closes_at=future(10)), headers=admin)

    jobs = client.get("/api/community/jobs", headers=auth(people["amina"])).json()

    assert [job["title"] for job in jobs] == ["Open role"]
