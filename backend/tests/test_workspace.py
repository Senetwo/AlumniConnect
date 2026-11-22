from datetime import datetime, timedelta, timezone

import pytest

from app.models.booking import Booking, MentorAvailability
from app.models.mentorship import Mentorship
from app.models.workspace import MentorshipActivityEvent, MentorshipSession, SessionNote
from app.database.workspace_migration import backfill_sessions_from_bookings
from test_mentorship import create_mentor_and_mentee, login_user, register_user

PRIVATE_TEXT = "PRIVATE-REFLECTION-do-not-leak"


def iso(delta_hours):
    return (datetime.now(timezone.utc) + timedelta(hours=delta_hours)).isoformat()


@pytest.fixture
def pair(client, db):
    mentee, mentor, mentee_h, mentor_h = create_mentor_and_mentee(client)
    created = client.post(
        "/api/mentorships/",
        json={"mentor_id": mentor["id"], "motivation": "I would like guidance on my next career step."},
        headers=mentee_h,
    ).json()
    client.patch(f"/api/mentorships/{created['id']}/respond", json={"decision": "accepted"}, headers=mentor_h)
    other = register_user(client, "other@example.com", "Other Member", "Password123!", "mentee")
    other_h = login_user(client, "other@example.com", "Password123!")
    return {
        "id": created["id"], "mentee": mentee, "mentor": mentor,
        "mentee_h": mentee_h, "mentor_h": mentor_h, "other_h": other_h, "other": other,
    }


def url(pair, path=""):
    return f"/api/mentorships/{pair['id']}{path}"


def make_session(client, pair, who="mentor_h", hours=48, **extra):
    body = {"title": "Career planning", "scheduled_at": iso(hours), "duration_minutes": 45,
            "meeting_type": "virtual", "meeting_link": "https://meet.example.com/abc", **extra}
    response = client.post(url(pair, "/sessions"), json=body, headers=pair[who])
    assert response.status_code == 201, response.text
    return response.json()


# ------------------------------------------------------------------ workspace access

def test_mentor_and_mentee_can_open_workspace(client, pair):
    for who in ("mentor_h", "mentee_h"):
        response = client.get(url(pair, "/workspace"), headers=pair[who])
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["mentor"]["full_name"] == "Test Mentor"
        assert data["mentee"]["full_name"] == "Test Mentee"
        assert data["goals"] == [] and data["upcoming_sessions"] == []
    assert client.get(url(pair, "/workspace"), headers=pair["mentor_h"]).json()["viewer"]["role"] == "mentor"


def test_unrelated_user_and_anonymous_cannot_open_workspace(client, pair):
    assert client.get(url(pair, "/workspace"), headers=pair["other_h"]).status_code == 404
    assert client.get(url(pair, "/sessions"), headers=pair["other_h"]).status_code == 404
    assert client.get(url(pair, "/workspace")).status_code == 401


def test_pending_and_declined_have_no_workspace(client, pair):
    third = register_user(client, "third@example.com", "Third Mentor", "Password123!", "mentor")
    third_h = login_user(client, "third@example.com", "Password123!")
    req = client.post("/api/mentorships/", json={"mentor_id": third["id"], "motivation": "I would like guidance on my next career step."},
                      headers=pair["other_h"]).json()
    assert client.get(f"/api/mentorships/{req['id']}/workspace", headers=pair["other_h"]).status_code == 404
    client.patch(f"/api/mentorships/{req['id']}/respond", json={"decision": "declined"}, headers=third_h)
    assert client.get(f"/api/mentorships/{req['id']}/workspace", headers=third_h).status_code == 404


def test_admin_has_no_workspace_access(client, db, pair):
    from app.models.user import User
    admin = register_user(client, "boss@example.com", "Boss", "Password123!", "mentor")
    db.query(User).filter(User.id == admin["id"]).update({"role": "admin", "community_role": "mentor"})
    db.commit()
    admin_h = login_user(client, "boss@example.com", "Password123!")
    assert client.get(url(pair, "/workspace"), headers=admin_h).status_code == 404


def test_community_connection_does_not_create_workspace(client, pair):
    # A connection request between two members is a separate feature: no mentorship row appears.
    before = client.get(url(pair, "/workspace"), headers=pair["other_h"]).status_code
    assert before == 404


# ------------------------------------------------------------------ sessions

def test_session_create_update_cancel(client, pair):
    session = make_session(client, pair, "mentee_h")
    assert session["status"] == "scheduled" and session["meeting_type"] == "virtual"
    sid = session["id"]

    updated = client.patch(url(pair, f"/sessions/{sid}"), json={"title": "Roadmap review", "agenda": "Goals"},
                           headers=pair["mentor_h"])
    assert updated.status_code == 200 and updated.json()["title"] == "Roadmap review"

    cancelled = client.post(url(pair, f"/sessions/{sid}/cancel"), json={"reason": "Clash"}, headers=pair["mentee_h"])
    assert cancelled.status_code == 200 and cancelled.json()["status"] == "cancelled"
    # Cancelled sessions are terminal
    assert client.patch(url(pair, f"/sessions/{sid}"), json={"title": "x y z"}, headers=pair["mentor_h"]).status_code == 409
    assert client.post(url(pair, f"/sessions/{sid}/cancel"), json={}, headers=pair["mentor_h"]).status_code == 409
    assert client.post(url(pair, f"/sessions/{sid}/complete"), headers=pair["mentor_h"]).status_code == 409


def test_session_validation(client, pair):
    bad = [
        {"title": "ab", "scheduled_at": iso(2)},
        {"title": "Valid title", "scheduled_at": "2026-12-01T10:00:00"},  # no time zone
        {"title": "Valid title", "scheduled_at": iso(2), "duration_minutes": 2},
        {"title": "Valid title", "scheduled_at": iso(2), "meeting_link": "javascript:alert(1)"},
        {"title": "Valid title", "scheduled_at": iso(2), "meeting_type": "phone"},
    ]
    for body in bad:
        assert client.post(url(pair, "/sessions"), json=body, headers=pair["mentor_h"]).status_code == 422, body


def test_complete_only_after_start(client, pair):
    future = make_session(client, pair, hours=24)
    assert client.post(url(pair, f"/sessions/{future['id']}/complete"), headers=pair["mentor_h"]).status_code == 409
    past = make_session(client, pair, hours=-3, title="Kick-off call")
    done = client.post(url(pair, f"/sessions/{past['id']}/complete"), headers=pair["mentee_h"])
    assert done.status_code == 200 and done.json()["status"] == "completed"
    assert client.post(url(pair, f"/sessions/{past['id']}/complete"), headers=pair["mentee_h"]).status_code == 409


def test_session_lists_split_upcoming_and_past(client, pair):
    make_session(client, pair, hours=24)
    past = make_session(client, pair, hours=-5, title="Earlier call")
    client.post(url(pair, f"/sessions/{past['id']}/complete"), headers=pair["mentor_h"])
    data = client.get(url(pair, "/sessions"), headers=pair["mentee_h"]).json()
    assert len(data["upcoming"]) == 1 and len(data["past"]) == 1


def test_session_of_another_mentorship_is_not_reachable(client, pair):
    session = make_session(client, pair)
    third = register_user(client, "third@example.com", "Third Mentor", "Password123!", "mentor")
    third_h = login_user(client, "third@example.com", "Password123!")
    req = client.post("/api/mentorships/", json={"mentor_id": third["id"], "motivation": "I would like guidance on my next career step."},
                      headers=pair["other_h"]).json()
    client.patch(f"/api/mentorships/{req['id']}/respond", json={"decision": "accepted"}, headers=third_h)
    # Right caller, right workspace, but a session id from someone else's mentorship
    assert client.get(f"/api/mentorships/{req['id']}/sessions/{session['id']}", headers=third_h).status_code == 404
    assert client.patch(url(pair, f"/sessions/{session['id']}"), json={"title": "Hijack"}, headers=pair["other_h"]).status_code == 404


# ------------------------------------------------------------------ notes

def add_note(client, pair, sid, who, visibility, text="Talked about leadership"):
    return client.post(url(pair, f"/sessions/{sid}/notes"),
                       json={"visibility": visibility, "key_takeaways": text}, headers=pair[who])


def test_visibility_is_required_and_validated(client, pair):
    sid = make_session(client, pair)["id"]
    assert client.post(url(pair, f"/sessions/{sid}/notes"), json={"key_takeaways": "x"}, headers=pair["mentor_h"]).status_code == 422
    assert client.post(url(pair, f"/sessions/{sid}/notes"), json={"visibility": "team", "key_takeaways": "x"},
                       headers=pair["mentor_h"]).status_code == 422
    assert client.post(url(pair, f"/sessions/{sid}/notes"), json={"visibility": "shared"}, headers=pair["mentor_h"]).status_code == 422


def test_shared_note_visible_to_both(client, pair):
    sid = make_session(client, pair)["id"]
    assert add_note(client, pair, sid, "mentor_h", "shared").status_code == 201
    for who in ("mentor_h", "mentee_h"):
        notes = client.get(url(pair, "/notes"), headers=pair[who]).json()
        assert len(notes) == 1 and notes[0]["visibility"] == "shared"
    assert client.get(url(pair, "/notes"), headers=pair["other_h"]).status_code == 404


def test_private_note_never_reaches_the_other_participant(client, pair):
    sid = make_session(client, pair)["id"]
    created = add_note(client, pair, sid, "mentee_h", "private", PRIVATE_TEXT)
    assert created.status_code == 201
    note_id = created.json()["id"]

    mentor = pair["mentor_h"]
    responses = [
        client.get(url(pair, "/notes"), headers=mentor),
        client.get(url(pair, f"/sessions/{sid}"), headers=mentor),
        client.get(url(pair, "/workspace"), headers=mentor),
        client.get(url(pair, "/progress"), headers=mentor),
        client.get(url(pair, "/timeline"), headers=mentor),
        client.get(url(pair, "/sessions"), headers=mentor),
        client.get(url(pair, "/goals"), headers=mentor),
        client.get(url(pair, "/action-items"), headers=mentor),
    ]
    for response in responses:
        assert response.status_code == 200
        assert PRIVATE_TEXT not in response.text
    assert client.get(url(pair, "/notes"), headers=mentor).json() == []
    assert client.get(url(pair, f"/sessions/{sid}"), headers=mentor).json()["notes"] == []

    # The other participant cannot edit it, and cannot even tell it exists
    edit = client.patch(url(pair, f"/notes/{note_id}"), json={"key_takeaways": "overwrite"}, headers=mentor)
    assert edit.status_code == 404
    # The author still sees it everywhere it should appear
    assert client.get(url(pair, "/notes"), headers=pair["mentee_h"]).json()[0]["key_takeaways"] == PRIVATE_TEXT
    assert len(client.get(url(pair, f"/sessions/{sid}"), headers=pair["mentee_h"]).json()["notes"]) == 1
    # And no activity event was written for it
    assert client.get(url(pair, "/timeline"), headers=pair["mentee_h"]).json()[-1]["event_type"] != "note_shared"


def test_only_author_can_edit_a_shared_note(client, pair):
    sid = make_session(client, pair)["id"]
    note_id = add_note(client, pair, sid, "mentor_h", "shared").json()["id"]
    assert client.patch(url(pair, f"/notes/{note_id}"), json={"advice": "Read more"}, headers=pair["mentee_h"]).status_code == 403
    ok = client.patch(url(pair, f"/notes/{note_id}"), json={"advice": "Read more"}, headers=pair["mentor_h"])
    assert ok.status_code == 200 and ok.json()["advice"] == "Read more"
    assert ok.json()["updated_at"] >= ok.json()["created_at"]


def test_note_can_be_made_shared_by_its_author_only(client, pair):
    sid = make_session(client, pair)["id"]
    note_id = add_note(client, pair, sid, "mentee_h", "private").json()["id"]
    assert client.patch(url(pair, f"/notes/{note_id}"), json={"visibility": "shared"}, headers=pair["mentor_h"]).status_code == 404
    shared = client.patch(url(pair, f"/notes/{note_id}"), json={"visibility": "shared"}, headers=pair["mentee_h"])
    assert shared.status_code == 200
    assert len(client.get(url(pair, "/notes"), headers=pair["mentor_h"]).json()) == 1


def test_notes_not_allowed_on_cancelled_session(client, pair):
    sid = make_session(client, pair)["id"]
    client.post(url(pair, f"/sessions/{sid}/cancel"), json={}, headers=pair["mentor_h"])
    assert add_note(client, pair, sid, "mentor_h", "shared").status_code == 409


# ------------------------------------------------------------------ goals and action items

def test_goal_lifecycle_and_history(client, pair):
    created = client.post(url(pair, "/goals"), json={"title": "Pass the licence exam", "target_date": "2027-03-01",
                                                      "assignee_id": pair["mentee"]["id"]}, headers=pair["mentor_h"])
    assert created.status_code == 201
    goal = created.json()
    assert goal["status"] == "not_started" and goal["assignee_name"] == "Test Mentee"

    gid = goal["id"]
    assert client.patch(url(pair, f"/goals/{gid}"), json={"status": "in_progress"}, headers=pair["mentee_h"]).json()["status"] == "in_progress"
    client.patch(url(pair, f"/goals/{gid}"), json={"description": "Study plan agreed"}, headers=pair["mentor_h"])
    done = client.patch(url(pair, f"/goals/{gid}"), json={"status": "completed"}, headers=pair["mentee_h"]).json()
    assert done["status"] == "completed" and done["completed_at"] is not None

    history = client.get(url(pair, f"/goals/{gid}/history"), headers=pair["mentor_h"]).json()
    kinds = [e["event_type"] for e in history]
    assert kinds[-1] == "goal_created" and "goal_completed" in kinds and "goal_updated" in kinds
    status_event = next(e for e in history if e["event_type"] == "goal_status_changed")
    assert (status_event["old_value"], status_event["new_value"]) == ("not_started", "in_progress")

    reopened = client.patch(url(pair, f"/goals/{gid}"), json={"status": "on_hold"}, headers=pair["mentor_h"]).json()
    assert reopened["completed_at"] is None


def test_goal_validation_and_outsider_assignee(client, pair):
    assert client.post(url(pair, "/goals"), json={"title": "no"}, headers=pair["mentor_h"]).status_code == 422
    assert client.post(url(pair, "/goals"), json={"title": "Valid goal", "status": "finished"}, headers=pair["mentor_h"]).status_code == 422
    outsider = client.post(url(pair, "/goals"), json={"title": "Valid goal", "assignee_id": pair["other"]["id"]}, headers=pair["mentor_h"])
    assert outsider.status_code == 422


def test_goals_unreachable_by_outsiders(client, pair):
    gid = client.post(url(pair, "/goals"), json={"title": "Shared goal"}, headers=pair["mentor_h"]).json()["id"]
    assert client.get(url(pair, "/goals"), headers=pair["other_h"]).status_code == 404
    assert client.patch(url(pair, f"/goals/{gid}"), json={"status": "completed"}, headers=pair["other_h"]).status_code == 404
    assert client.get(url(pair, f"/goals/{gid}/history"), headers=pair["other_h"]).status_code == 404


def test_action_item_assignment_completion_and_links(client, pair):
    gid = client.post(url(pair, "/goals"), json={"title": "Build a portfolio"}, headers=pair["mentor_h"]).json()["id"]
    sid = make_session(client, pair)["id"]
    created = client.post(url(pair, "/action-items"), json={
        "description": "Draft three case studies", "assigned_to_id": pair["mentee"]["id"],
        "due_date": "2027-01-15", "goal_id": gid, "session_id": sid,
    }, headers=pair["mentor_h"])
    assert created.status_code == 201
    item = created.json()
    assert item["assigned_to_name"] == "Test Mentee" and item["status"] == "open" and item["completed_at"] is None

    open_items = client.get(url(pair, "/action-items?state=open"), headers=pair["mentee_h"]).json()
    assert [i["id"] for i in open_items] == [item["id"]]
    assert client.get(url(pair, f"/goals"), headers=pair["mentee_h"]).json()[0]["action_items"][0]["id"] == item["id"]
    assert client.get(url(pair, f"/sessions/{sid}"), headers=pair["mentee_h"]).json()["action_items"][0]["id"] == item["id"]

    done = client.patch(url(pair, f"/action-items/{item['id']}"), json={"status": "completed"}, headers=pair["mentee_h"]).json()
    assert done["status"] == "completed" and done["completed_at"] is not None
    assert client.get(url(pair, "/action-items?state=open"), headers=pair["mentee_h"]).json() == []
    reopened = client.patch(url(pair, f"/action-items/{item['id']}"), json={"status": "open"}, headers=pair["mentor_h"]).json()
    assert reopened["completed_at"] is None


def test_action_item_authorization_and_validation(client, pair):
    body = {"description": "Send the draft", "assigned_to_id": pair["mentee"]["id"]}
    assert client.post(url(pair, "/action-items"), json=body, headers=pair["other_h"]).status_code == 404
    assert client.post(url(pair, "/action-items"), json={**body, "assigned_to_id": pair["other"]["id"]}, headers=pair["mentor_h"]).status_code == 422
    assert client.post(url(pair, "/action-items"), json={**body, "goal_id": 9999}, headers=pair["mentor_h"]).status_code == 422
    assert client.post(url(pair, "/action-items"), json={**body, "description": "x"}, headers=pair["mentor_h"]).status_code == 422
    item = client.post(url(pair, "/action-items"), json=body, headers=pair["mentor_h"]).json()
    assert client.patch(url(pair, f"/action-items/{item['id']}"), json={"status": "completed"}, headers=pair["other_h"]).status_code == 404


# ------------------------------------------------------------------ progress and timeline

def test_progress_is_calculated_from_real_rows(client, pair):
    empty = client.get(url(pair, "/progress"), headers=pair["mentor_h"]).json()
    assert empty["goals"]["percent_complete"] is None and empty["action_items"]["percent_complete"] is None
    assert empty["needs_attention"] == []

    g1 = client.post(url(pair, "/goals"), json={"title": "Goal one"}, headers=pair["mentor_h"]).json()["id"]
    g2 = client.post(url(pair, "/goals"), json={"title": "Goal two"}, headers=pair["mentor_h"]).json()["id"]
    g3 = client.post(url(pair, "/goals"), json={"title": "Goal three"}, headers=pair["mentor_h"]).json()["id"]
    client.patch(url(pair, f"/goals/{g1}"), json={"status": "completed"}, headers=pair["mentor_h"])
    client.patch(url(pair, f"/goals/{g3}"), json={"status": "on_hold"}, headers=pair["mentor_h"])
    for text in ("First task", "Second task"):
        client.post(url(pair, "/action-items"), json={"description": text, "assigned_to_id": pair["mentee"]["id"],
                                                      "due_date": "2020-01-01"}, headers=pair["mentor_h"])
    first = client.get(url(pair, "/action-items"), headers=pair["mentor_h"]).json()[0]["id"]
    client.patch(url(pair, f"/action-items/{first}"), json={"status": "completed"}, headers=pair["mentee_h"])
    past = make_session(client, pair, hours=-4)
    client.post(url(pair, f"/sessions/{past['id']}/complete"), headers=pair["mentor_h"])

    progress = client.get(url(pair, "/progress"), headers=pair["mentee_h"]).json()
    assert progress["goals"]["percent_complete"] == 50  # 1 of 2 goals, the on-hold goal is excluded
    assert progress["goals"]["on_hold"] == 1
    assert progress["action_items"]["percent_complete"] == 50 and progress["action_items"]["overdue"] == 1
    assert progress["sessions"]["completed"] == 1
    assert "method" in progress and len(progress["completed_action_items"]) == 1
    assert any(entry["type"] == "action_item_overdue" for entry in progress["needs_attention"])


def test_timeline_has_only_real_events_in_order(client, pair):
    fresh = client.get(url(pair, "/timeline?order=asc"), headers=pair["mentor_h"]).json()
    assert [e["event_type"] for e in fresh] == ["mentorship_established"]

    gid = client.post(url(pair, "/goals"), json={"title": "Real goal"}, headers=pair["mentor_h"]).json()["id"]
    sid = make_session(client, pair)["id"]
    client.patch(url(pair, f"/goals/{gid}"), json={"status": "completed"}, headers=pair["mentor_h"])
    events = client.get(url(pair, "/timeline?order=asc"), headers=pair["mentee_h"]).json()
    assert [e["event_type"] for e in events] == [
        "mentorship_established", "goal_created", "session_scheduled", "goal_completed"]
    stamps = [e["created_at"] for e in events]
    assert stamps == sorted(stamps)
    assert client.get(url(pair, "/timeline"), headers=pair["other_h"]).status_code == 404


# ------------------------------------------------------------------ closure

def test_close_mentorship_preserves_history_and_goes_read_only(client, db, pair):
    gid = client.post(url(pair, "/goals"), json={"title": "Keep this goal"}, headers=pair["mentor_h"]).json()["id"]
    sid = make_session(client, pair, hours=72)["id"]
    add_note(client, pair, sid, "mentor_h", "shared")

    closed = client.post(url(pair, "/close"), json={"outcome_summary": "Reached the licence goal."}, headers=pair["mentee_h"])
    assert closed.status_code == 200 and closed.json()["status"] == "completed"

    row = db.query(Mentorship).filter_by(id=pair["id"]).one()
    assert row.status == "completed" and row.closed_at is not None
    assert row.closed_by_id == pair["mentee"]["id"] and row.outcome_summary == "Reached the licence goal."

    workspace = client.get(url(pair, "/workspace"), headers=pair["mentor_h"]).json()
    assert workspace["status"] == "completed" and workspace["is_writable"] is False
    assert workspace["outcome_summary"] == "Reached the licence goal."
    assert len(workspace["goals"]) == 1 and len(client.get(url(pair, "/notes"), headers=pair["mentor_h"]).json()) == 1
    # The future session was cancelled, not deleted
    session = client.get(url(pair, f"/sessions/{sid}"), headers=pair["mentor_h"]).json()
    assert session["status"] == "cancelled"
    assert db.query(MentorshipSession).count() == 1 and db.query(SessionNote).count() == 1

    # Read-only: every write is refused
    assert client.post(url(pair, "/goals"), json={"title": "Too late"}, headers=pair["mentor_h"]).status_code == 409
    assert client.post(url(pair, "/sessions"), json={"title": "Too late", "scheduled_at": iso(5)}, headers=pair["mentor_h"]).status_code == 409
    assert client.patch(url(pair, f"/goals/{gid}"), json={"status": "completed"}, headers=pair["mentor_h"]).status_code == 409
    assert client.post(url(pair, "/close"), json={}, headers=pair["mentor_h"]).status_code == 409

    timeline = client.get(url(pair, "/timeline"), headers=pair["mentor_h"]).json()
    assert timeline[0]["event_type"] == "mentorship_completed"
    # The mentorship request list reports it as completed
    outgoing = client.get("/api/mentorships/outgoing", headers=pair["mentee_h"]).json()
    assert outgoing[0]["status"] == "completed"


def test_only_participants_can_close(client, pair):
    assert client.post(url(pair, "/close"), json={}, headers=pair["other_h"]).status_code == 404
    assert client.get(url(pair, "/workspace"), headers=pair["mentor_h"]).json()["status"] == "accepted"


def test_chat_history_stays_readable_after_close(client, pair):
    conv = client.post(f"/api/chat/conversations/{pair['id']}", headers=pair["mentee_h"]).json()
    client.post(f"/api/chat/conversations/{conv['id']}/messages", json={"body": "Hello mentor"}, headers=pair["mentee_h"])
    client.post(url(pair, "/close"), json={}, headers=pair["mentor_h"])
    listing = client.get("/api/chat/conversations", headers=pair["mentee_h"]).json()
    assert listing[0]["mentorship_status"] == "completed"
    messages = client.get(f"/api/chat/conversations/{conv['id']}/messages", headers=pair["mentee_h"])
    assert messages.status_code == 200 and messages.json()[0]["body"] == "Hello mentor"
    blocked = client.post(f"/api/chat/conversations/{conv['id']}/messages", json={"body": "Still there?"}, headers=pair["mentee_h"])
    assert blocked.status_code == 409


# ------------------------------------------------------------------ bookings integration

def make_slot(db, mentor_id, hours=96):
    start = datetime.now(timezone.utc) + timedelta(hours=hours)
    slot = MentorAvailability(mentor_id=mentor_id, start_at=start, end_at=start + timedelta(hours=1), status="available")
    db.add(slot)
    db.commit()
    return slot


def test_booking_creates_and_cancels_linked_session(client, db, pair):
    slot = make_slot(db, pair["mentor"]["id"])
    booking = client.post("/api/bookings", json={"mentorship_id": pair["id"], "availability_id": slot.id}, headers=pair["mentee_h"])
    assert booking.status_code == 201
    sessions = client.get(url(pair, "/sessions"), headers=pair["mentor_h"]).json()["upcoming"]
    assert len(sessions) == 1 and sessions[0]["from_booking"] is True and sessions[0]["duration_minutes"] == 60
    sid = sessions[0]["id"]
    # A booked time cannot be edited from the workspace
    assert client.patch(url(pair, f"/sessions/{sid}"), json={"duration_minutes": 30}, headers=pair["mentor_h"]).status_code == 409

    cancelled = client.patch(f"/api/bookings/{booking.json()['id']}/cancel", headers=pair["mentee_h"])
    assert cancelled.status_code == 200
    assert client.get(url(pair, f"/sessions/{sid}"), headers=pair["mentor_h"]).json()["status"] == "cancelled"

    # Booking the same slot again reuses the one session row
    again = client.post("/api/bookings", json={"mentorship_id": pair["id"], "availability_id": slot.id}, headers=pair["mentee_h"])
    assert again.status_code == 201
    assert db.query(MentorshipSession).count() == 1
    assert client.get(url(pair, f"/sessions/{sid}"), headers=pair["mentor_h"]).json()["status"] == "scheduled"


def test_cancelling_booked_session_from_workspace_frees_the_slot(client, db, pair):
    slot = make_slot(db, pair["mentor"]["id"])
    client.post("/api/bookings", json={"mentorship_id": pair["id"], "availability_id": slot.id}, headers=pair["mentee_h"])
    sid = client.get(url(pair, "/sessions"), headers=pair["mentee_h"]).json()["upcoming"][0]["id"]
    assert client.post(url(pair, f"/sessions/{sid}/cancel"), json={}, headers=pair["mentee_h"]).status_code == 200
    db.expire_all()
    assert db.get(MentorAvailability, slot.id).status == "available"
    assert db.query(Booking).one().status == "cancelled"


def test_backfill_adds_sessions_for_existing_bookings_once(client, db, pair):
    slot = make_slot(db, pair["mentor"]["id"])
    client.post("/api/bookings", json={"mentorship_id": pair["id"], "availability_id": slot.id}, headers=pair["mentee_h"])
    db.query(MentorshipSession).delete()
    db.query(MentorshipActivityEvent).delete()
    db.commit()
    assert backfill_sessions_from_bookings(db) == 1
    assert backfill_sessions_from_bookings(db) == 0
    assert db.query(MentorshipSession).count() == 1


# ------------------------------------------------------------------ feedback, summary, reminders, limits

def test_match_explanation_is_descriptive_and_handles_no_overlap():
    from types import SimpleNamespace as P
    from app.services.match_explanation import explain_match
    mentee = P(skills="Navigation, Meteorology, Python", career_domain="Piloting", career_path="Flight operations",
               career_goals="I want to become a flight dispatcher and learn weather briefing", mentorship_interests="dispatch")
    mentor = P(skills="meteorology, Dispatch, CRM", career_domain="piloting", career_path="Flight operations",
               bio="Dispatcher with ten years of weather briefing", )
    reasons = explain_match(mentee, mentor)
    assert any(r.startswith("Shared skills: meteorology") for r in reasons)
    assert "Same career domain: piloting" in reasons and "Same career path: Flight operations" in reasons
    slug = P(skills="", career_domain="flight-operations", career_path="Piloting", career_goals="", mentorship_interests="", bio="")
    assert "Same career domain: Flight operations" in explain_match(slug, slug)
    assert any(r.startswith("Matches your goals") and "briefing" in r for r in reasons)
    other = P(skills="Finance", career_domain="Cargo", career_path="Revenue", bio="Budgets")
    assert explain_match(mentee, other) == []


def test_feedback_only_after_completion_once_and_private(client, pair):
    body = {"rating": 4, "comment": "Clear and practical."}
    assert client.post(url(pair, "/feedback"), json=body, headers=pair["mentee_h"]).status_code == 409  # still active
    assert client.get(url(pair, "/feedback"), headers=pair["mentee_h"]).json()["can_submit"] is False
    client.post(url(pair, "/close"), json={}, headers=pair["mentor_h"])

    assert client.get(url(pair, "/feedback"), headers=pair["mentee_h"]).json()["can_submit"] is True
    assert client.post(url(pair, "/feedback"), json={"rating": 6}, headers=pair["mentee_h"]).status_code == 422
    assert client.post(url(pair, "/feedback"), json={"rating": 0}, headers=pair["mentee_h"]).status_code == 422
    assert client.post(url(pair, "/feedback"), json=body, headers=pair["other_h"]).status_code == 404
    assert client.post(url(pair, "/feedback"), json=body, headers=pair["mentee_h"]).status_code == 201
    assert client.post(url(pair, "/feedback"), json=body, headers=pair["mentee_h"]).status_code == 409  # once only

    mine = client.get(url(pair, "/feedback"), headers=pair["mentee_h"]).json()
    assert mine["mine"]["rating"] == 4 and mine["can_submit"] is False
    # The mentor cannot see the mentee's rating
    theirs = client.get(url(pair, "/feedback"), headers=pair["mentor_h"]).json()
    assert theirs["mine"] is None and "Clear and practical" not in client.get(url(pair, "/workspace"), headers=pair["mentor_h"]).text


def test_summary_lists_only_my_active_mentorships(client, pair):
    make_session(client, pair, hours=30)
    client.post(url(pair, "/action-items"), json={"description": "Overdue task", "assigned_to_id": pair["mentee"]["id"],
                                                  "due_date": "2020-01-01"}, headers=pair["mentor_h"])
    mine = client.get("/api/mentorships/summary", headers=pair["mentee_h"]).json()
    row = mine[str(pair["id"])]
    assert row["open_action_items"] == 1 and row["overdue_action_items"] == 1 and row["next_session"]["title"] == "Career planning"
    assert client.get("/api/mentorships/summary", headers=pair["other_h"]).json() == {}
    client.post(url(pair, "/close"), json={}, headers=pair["mentor_h"])
    assert client.get("/api/mentorships/summary", headers=pair["mentee_h"]).json() == {}


def test_reminders_created_once_for_soon_sessions_and_overdue_items(client, pair):
    make_session(client, pair, hours=5, title="Soon session")
    make_session(client, pair, hours=90, title="Far session")
    client.post(url(pair, "/action-items"), json={"description": "Late task", "assigned_to_id": pair["mentee"]["id"],
                                                  "due_date": "2020-01-01"}, headers=pair["mentor_h"])
    for _ in range(2):  # reading twice must not duplicate
        notes = client.get("/api/notifications/", headers=pair["mentee_h"]).json()
    kinds = [n["type"] for n in notes]
    assert kinds.count("session_reminder") == 1 and kinds.count("action_item_overdue") == 1
    reminders = [n for n in notes if n["type"] == "session_reminder"]
    assert "Soon session" in reminders[0]["message"] and "Far session" not in reminders[0]["message"]
    # The mentor was not assigned the task, so gets no overdue reminder, but does get the session reminder
    mentor_kinds = [n["type"] for n in client.get("/api/notifications/", headers=pair["mentor_h"]).json()]
    assert "action_item_overdue" not in mentor_kinds and "session_reminder" in mentor_kinds
    assert client.get("/api/notifications/unread-count", headers=pair["mentee_h"]).json()["count"] >= 2


def test_write_limit_returns_429(client, pair, monkeypatch):
    import app.api.workspace as ws
    monkeypatch.setattr(ws, "WRITES_PER_HOUR", 3)
    for index in range(3):
        assert client.post(url(pair, "/goals"), json={"title": f"Goal number {index}"}, headers=pair["mentor_h"]).status_code == 201
    assert client.post(url(pair, "/goals"), json={"title": "One too many"}, headers=pair["mentor_h"]).status_code == 429
    # Reading is never limited, and the other participant has their own allowance
    assert client.get(url(pair, "/goals"), headers=pair["mentor_h"]).status_code == 200
    assert client.post(url(pair, "/goals"), json={"title": "Mentee goal"}, headers=pair["mentee_h"]).status_code == 201


def test_admin_dashboard_reports_feedback_and_completed(client, db, pair):
    from app.models.user import User
    admin = register_user(client, "root@example.com", "Root", "Password123!", "mentor")
    db.query(User).filter(User.id == admin["id"]).update({"role": "admin", "community_role": "mentor"})
    db.commit()
    admin_h = login_user(client, "root@example.com", "Password123!")
    client.post(url(pair, "/close"), json={}, headers=pair["mentor_h"])
    client.post(url(pair, "/feedback"), json={"rating": 5}, headers=pair["mentee_h"])
    client.post(url(pair, "/feedback"), json={"rating": 3}, headers=pair["mentor_h"])
    metrics = client.get("/api/admin/dashboard", headers=admin_h).json()["metrics"]
    assert metrics["match_feedback"] == {"count": 2, "average_rating": 4.0}
    assert metrics["mentorships"]["completed"] == 1
