"""Mentorship workspace: sessions, meeting notes, goals, action items, progress, timeline, closure.

Access rule used by every route: the caller must be the mentor or the mentee of the
mentorship. Anyone else gets 404, so ids cannot be probed. Writes need an accepted
mentorship; a completed one is read-only. Administrators get no extra access here.
"""
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.booking import Booking, MentorAvailability
from app.models.mentorship import Mentorship
from app.models.profile import Profile
from app.models.user import User
from app.models.workspace import (
    ActionItem,
    MentorshipActivityEvent,
    MentorshipFeedback,
    MentorshipGoal,
    MentorshipSession,
    SessionNote,
)
from app.schemas.workspace import (
    NOTE_FIELDS,
    ActionItemCreate,
    ActionItemUpdate,
    CloseMentorship,
    FeedbackCreate,
    GoalCreate,
    GoalUpdate,
    NoteCreate,
    NoteUpdate,
    SessionCancel,
    SessionCreate,
    SessionUpdate,
)
from app.services.notification_service import create_notification

router = APIRouter(prefix="/api/mentorships", tags=["Mentorship workspace"])

EAT = timezone(timedelta(hours=3))  # East Africa Time, no daylight saving
RECENT_LIMIT = 5
WRITES_PER_HOUR = 200


# ---------------------------------------------------------------- helpers

def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def today_eat() -> date:
    return datetime.now(EAT).date()


def load_mentorship(db: Session, mentorship_id: int, user: User, *, writable: bool = False) -> Mentorship:
    mentorship = (
        db.query(Mentorship)
        .filter(
            Mentorship.id == mentorship_id,
            or_(Mentorship.mentor_id == user.id, Mentorship.mentee_id == user.id),
            Mentorship.status.in_(["accepted", "completed"]),
        )
        .first()
    )
    if mentorship is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mentorship workspace not found.")
    if writable and mentorship.status != "accepted":
        raise HTTPException(status.HTTP_409_CONFLICT, "This mentorship is closed, so its workspace is read-only.")
    if writable:
        enforce_write_limit(db, user)
    return mentorship


def enforce_write_limit(db: Session, user: User) -> None:
    """Stops a runaway client or script. Counted from rows that already exist."""
    since = now_utc() - timedelta(hours=1)
    recent = (
        db.query(MentorshipActivityEvent.id)
        .filter(MentorshipActivityEvent.actor_id == user.id, MentorshipActivityEvent.created_at >= since).count()
        + db.query(SessionNote.id).filter(SessionNote.author_id == user.id, SessionNote.created_at >= since).count()
    )
    if recent >= WRITES_PER_HOUR:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "You have made many changes recently. Please try again later.")


def other_party_id(mentorship: Mentorship, user: User) -> int:
    return mentorship.mentee_id if user.id == mentorship.mentor_id else mentorship.mentor_id


def user_name(db: Session, user_id: int | None) -> str | None:
    if user_id is None:
        return None
    user = db.get(User, user_id)
    return user.full_name if user else None


def record(db: Session, mentorship: Mentorship, actor: User, event_type: str, summary: str, *,
           entity_type: str | None = None, entity_id: int | None = None,
           old_value: str | None = None, new_value: str | None = None) -> None:
    db.add(MentorshipActivityEvent(
        mentorship_id=mentorship.id, actor_id=actor.id, event_type=event_type, summary=summary[:300],
        entity_type=entity_type, entity_id=entity_id, old_value=old_value, new_value=new_value,
    ))


def notify_other(db: Session, mentorship: Mentorship, actor: User, kind: str, title: str, message: str) -> None:
    create_notification(
        db, user_id=other_party_id(mentorship, actor), notification_type=kind, title=title,
        message=message, resource_type="mentorship", resource_id=mentorship.id,
    )


def get_session_or_404(db: Session, mentorship: Mentorship, session_id: int) -> MentorshipSession:
    session = (
        db.query(MentorshipSession)
        .filter(MentorshipSession.id == session_id, MentorshipSession.mentorship_id == mentorship.id)
        .first()
    )
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found.")
    return session


def check_participant(mentorship: Mentorship, user_id: int | None, label: str) -> None:
    if user_id is not None and user_id not in (mentorship.mentor_id, mentorship.mentee_id):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"{label} must be the mentor or the mentee.")


def check_goal_and_session(db: Session, mentorship: Mentorship, goal_id: int | None, session_id: int | None) -> None:
    if goal_id is not None and not db.query(MentorshipGoal.id).filter(
        MentorshipGoal.id == goal_id, MentorshipGoal.mentorship_id == mentorship.id
    ).first():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "That goal does not belong to this mentorship.")
    if session_id is not None and not db.query(MentorshipSession.id).filter(
        MentorshipSession.id == session_id, MentorshipSession.mentorship_id == mentorship.id
    ).first():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "That session does not belong to this mentorship.")


# ---------------------------------------------------------------- serialisers

def session_dict(session: MentorshipSession) -> dict:
    start = as_utc(session.scheduled_at)
    return {
        "id": session.id,
        "mentorship_id": session.mentorship_id,
        "title": session.title,
        "description": session.description,
        "scheduled_at": start,
        "ends_at": start + timedelta(minutes=session.duration_minutes),
        "duration_minutes": session.duration_minutes,
        "meeting_type": session.meeting_type,
        "location": session.location,
        "meeting_link": session.meeting_link,
        "agenda": session.agenda,
        "status": session.status,
        "cancel_reason": session.cancel_reason,
        "from_booking": session.booking_id is not None,
        "created_by_id": session.created_by_id,
        "created_at": as_utc(session.created_at),
        "updated_at": as_utc(session.updated_at),
    }


def note_dict(db: Session, note: SessionNote, viewer: User, session_title: str | None = None) -> dict:
    return {
        "id": note.id,
        "session_id": note.session_id,
        "session_title": session_title,
        "author_id": note.author_id,
        "author_name": user_name(db, note.author_id),
        "is_mine": note.author_id == viewer.id,
        "visibility": note.visibility,
        **{name: getattr(note, name) for name in NOTE_FIELDS},
        "created_at": as_utc(note.created_at),
        "updated_at": as_utc(note.updated_at),
    }


def action_dict(db: Session, item: ActionItem) -> dict:
    due = item.due_date
    return {
        "id": item.id,
        "description": item.description,
        "assigned_to_id": item.assigned_to_id,
        "assigned_to_name": user_name(db, item.assigned_to_id),
        "due_date": due,
        "status": item.status,
        "is_overdue": item.status == "open" and due is not None and due < today_eat(),
        "goal_id": item.goal_id,
        "session_id": item.session_id,
        "created_by_id": item.created_by_id,
        "created_at": as_utc(item.created_at),
        "completed_at": as_utc(item.completed_at),
    }


def goal_dict(db: Session, goal: MentorshipGoal) -> dict:
    items = (
        db.query(ActionItem).filter(ActionItem.goal_id == goal.id)
        .order_by(ActionItem.status.desc(), ActionItem.due_date.asc(), ActionItem.id.asc()).all()
    )
    return {
        "id": goal.id,
        "title": goal.title,
        "description": goal.description,
        "target_date": goal.target_date,
        "status": goal.status,
        "assignee_id": goal.assignee_id,
        "assignee_name": user_name(db, goal.assignee_id) if goal.assignee_id else "Both",
        "is_overdue": goal.status != "completed" and goal.target_date is not None and goal.target_date < today_eat(),
        "created_by_id": goal.created_by_id,
        "created_at": as_utc(goal.created_at),
        "updated_at": as_utc(goal.updated_at),
        "completed_at": as_utc(goal.completed_at),
        "action_items": [action_dict(db, item) for item in items],
    }


def event_dict(db: Session, event: MentorshipActivityEvent) -> dict:
    return {
        "id": event.id,
        "event_type": event.event_type,
        "entity_type": event.entity_type,
        "entity_id": event.entity_id,
        "summary": event.summary,
        "old_value": event.old_value,
        "new_value": event.new_value,
        "actor_id": event.actor_id,
        "actor_name": user_name(db, event.actor_id),
        "created_at": as_utc(event.created_at),
    }


def party_dict(db: Session, user_id: int, role: str) -> dict:
    user = db.get(User, user_id)
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    return {
        "user_id": user_id,
        "role": role,
        "full_name": user.full_name if user else "Member",
        "career_domain": profile.career_domain if profile else None,
        "career_path": profile.career_path if profile else None,
        "experience": profile.experience if profile else None,
        "profile_picture_url": profile.profile_picture_url if profile else None,
    }


def visible_notes_query(db: Session, mentorship: Mentorship, viewer: User):
    """Shared notes plus the viewer's own private notes. The only place notes are read."""
    return db.query(SessionNote).filter(
        SessionNote.mentorship_id == mentorship.id,
        or_(SessionNote.visibility == "shared", SessionNote.author_id == viewer.id),
    )


# ---------------------------------------------------------------- progress

def compute_progress(db: Session, mentorship: Mentorship) -> dict:
    """Progress from stored rows only.

    goals.percent_complete  = completed goals / goals that are not on hold
    action_items.percent_complete = completed action items / all action items
    The two are reported separately and never blended. Sessions are counted as facts.
    """
    goals = db.query(MentorshipGoal).filter(MentorshipGoal.mentorship_id == mentorship.id).all()
    items = db.query(ActionItem).filter(ActionItem.mentorship_id == mentorship.id).all()
    sessions = db.query(MentorshipSession).filter(MentorshipSession.mentorship_id == mentorship.id).all()
    today = today_eat()
    now = now_utc()

    counted = [goal for goal in goals if goal.status != "on_hold"]
    done_goals = [goal for goal in counted if goal.status == "completed"]
    done_items = [item for item in items if item.status == "completed"]
    open_items = [item for item in items if item.status == "open"]

    attention = []
    for item in open_items:
        if item.due_date is not None and item.due_date < today:
            attention.append({"type": "action_item_overdue", "entity_type": "action_item", "entity_id": item.id,
                              "message": f"Overdue: {item.description}"})
    for goal in goals:
        if goal.status != "completed" and goal.target_date is not None and goal.target_date < today:
            attention.append({"type": "goal_past_target", "entity_type": "goal", "entity_id": goal.id,
                              "message": f"Goal past its target date: {goal.title}"})
    for session in sessions:
        if session.status == "scheduled" and as_utc(session.scheduled_at) + timedelta(minutes=session.duration_minutes) < now:
            attention.append({"type": "session_needs_update", "entity_type": "session", "entity_id": session.id,
                              "message": f"Mark as completed or cancelled: {session.title}"})

    return {
        "method": (
            "Goal progress is completed goals divided by goals that are not on hold. "
            "Action-item progress is completed items divided by all items. "
            "Neither figure is shown until there is at least one goal or item, and the number of sessions "
            "is reported as a count only; it is not a measure of how well the mentorship is going."
        ),
        "goals": {
            "total": len(goals),
            "not_started": sum(goal.status == "not_started" for goal in goals),
            "in_progress": sum(goal.status == "in_progress" for goal in goals),
            "completed": sum(goal.status == "completed" for goal in goals),
            "on_hold": sum(goal.status == "on_hold" for goal in goals),
            "percent_complete": round(100 * len(done_goals) / len(counted)) if counted else None,
        },
        "action_items": {
            "total": len(items),
            "open": len(open_items),
            "completed": len(done_items),
            "overdue": sum(1 for item in open_items if item.due_date is not None and item.due_date < today),
            "percent_complete": round(100 * len(done_items) / len(items)) if items else None,
        },
        "sessions": {
            "completed": sum(session.status == "completed" for session in sessions),
            "upcoming": sum(session.status == "scheduled" and as_utc(session.scheduled_at) >= now for session in sessions),
            "cancelled": sum(session.status == "cancelled" for session in sessions),
        },
        "needs_attention": attention,
    }


def timeline_events(db: Session, mentorship: Mentorship) -> list[dict]:
    """Stored events plus the two milestones that live on the mentorship row itself."""
    events = [
        event_dict(db, event)
        for event in db.query(MentorshipActivityEvent)
        .filter(MentorshipActivityEvent.mentorship_id == mentorship.id).all()
    ]
    if mentorship.responded_at is not None:
        events.append({
            "id": None, "event_type": "mentorship_established", "entity_type": "mentorship",
            "entity_id": mentorship.id, "summary": "Mentorship established", "old_value": None, "new_value": None,
            "actor_id": mentorship.mentor_id, "actor_name": user_name(db, mentorship.mentor_id),
            "created_at": as_utc(mentorship.responded_at),
        })
    if mentorship.closed_at is not None:
        events.append({
            "id": None, "event_type": "mentorship_completed", "entity_type": "mentorship",
            "entity_id": mentorship.id, "summary": "Mentorship completed", "old_value": None, "new_value": None,
            "actor_id": mentorship.closed_by_id, "actor_name": user_name(db, mentorship.closed_by_id),
            "created_at": as_utc(mentorship.closed_at),
        })
    events.sort(key=lambda event: event["created_at"])
    return events


# ---------------------------------------------------------------- summary across mentorships

@router.get("/summary")
def mentorship_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """One row per accepted mentorship the caller takes part in, for the list pages."""
    rows = (
        db.query(Mentorship)
        .filter(or_(Mentorship.mentor_id == current_user.id, Mentorship.mentee_id == current_user.id),
                Mentorship.status == "accepted")
        .all()
    )
    now, today = now_utc(), today_eat()
    summary = {}
    for mentorship in rows:
        items = db.query(ActionItem).filter(ActionItem.mentorship_id == mentorship.id, ActionItem.status == "open").all()
        upcoming = sorted(
            (s for s in db.query(MentorshipSession).filter(
                MentorshipSession.mentorship_id == mentorship.id, MentorshipSession.status == "scheduled")
             if as_utc(s.scheduled_at) >= now),
            key=lambda s: as_utc(s.scheduled_at),
        )
        summary[mentorship.id] = {
            "mentorship_id": mentorship.id,
            "open_action_items": len(items),
            "overdue_action_items": sum(1 for i in items if i.due_date is not None and i.due_date < today),
            "next_session": {"id": upcoming[0].id, "title": upcoming[0].title, "scheduled_at": as_utc(upcoming[0].scheduled_at)} if upcoming else None,
        }
    return summary


# ---------------------------------------------------------------- workspace

@router.get("/{mentorship_id}/workspace")
def get_workspace(
    mentorship_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user)
    now = now_utc()
    sessions = db.query(MentorshipSession).filter(MentorshipSession.mentorship_id == mentorship.id).all()
    upcoming = sorted(
        (s for s in sessions if s.status == "scheduled" and as_utc(s.scheduled_at) >= now),
        key=lambda s: as_utc(s.scheduled_at),
    )
    recent = sorted((s for s in sessions if s.status == "completed"), key=lambda s: as_utc(s.scheduled_at), reverse=True)
    goals = (
        db.query(MentorshipGoal).filter(MentorshipGoal.mentorship_id == mentorship.id)
        .order_by(MentorshipGoal.created_at.desc()).all()
    )
    outstanding = (
        db.query(ActionItem)
        .filter(ActionItem.mentorship_id == mentorship.id, ActionItem.status == "open")
        .order_by(ActionItem.due_date.asc(), ActionItem.id.asc()).all()
    )
    updates = timeline_events(db, mentorship)[-RECENT_LIMIT:][::-1]
    return {
        "id": mentorship.id,
        "status": mentorship.status,
        "is_writable": mentorship.status == "accepted",
        "started_at": as_utc(mentorship.responded_at or mentorship.created_at),
        "closed_at": as_utc(mentorship.closed_at),
        "closed_by_name": user_name(db, mentorship.closed_by_id),
        "outcome_summary": mentorship.outcome_summary,
        "viewer": {"user_id": current_user.id, "role": "mentor" if current_user.id == mentorship.mentor_id else "mentee"},
        "mentor": party_dict(db, mentorship.mentor_id, "mentor"),
        "mentee": party_dict(db, mentorship.mentee_id, "mentee"),
        "goals": [goal_dict(db, goal) for goal in goals],
        "upcoming_sessions": [session_dict(s) for s in upcoming[:RECENT_LIMIT]],
        "recent_sessions": [session_dict(s) for s in recent[:RECENT_LIMIT]],
        "outstanding_action_items": [action_dict(db, item) for item in outstanding],
        "recent_updates": updates,
        "progress": compute_progress(db, mentorship),
    }


# ---------------------------------------------------------------- sessions

@router.get("/{mentorship_id}/sessions")
def list_sessions(
    mentorship_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user)
    now = now_utc()
    rows = db.query(MentorshipSession).filter(MentorshipSession.mentorship_id == mentorship.id).all()
    upcoming = sorted((s for s in rows if s.status == "scheduled" and as_utc(s.scheduled_at) >= now),
                      key=lambda s: as_utc(s.scheduled_at))
    past = sorted((s for s in rows if s not in upcoming), key=lambda s: as_utc(s.scheduled_at), reverse=True)
    return {"upcoming": [session_dict(s) for s in upcoming], "past": [session_dict(s) for s in past]}


@router.post("/{mentorship_id}/sessions", status_code=status.HTTP_201_CREATED)
def create_session(
    mentorship_id: int,
    data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user, writable=True)
    session = MentorshipSession(
        mentorship_id=mentorship.id,
        created_by_id=current_user.id,
        title=data.title,
        description=data.description or None,
        scheduled_at=data.scheduled_at,
        duration_minutes=data.duration_minutes,
        meeting_type=data.meeting_type,
        location=(data.location or None) if data.meeting_type == "in_person" else None,
        meeting_link=data.meeting_link if data.meeting_type == "virtual" else None,
        agenda=data.agenda or None,
        status="scheduled",
    )
    db.add(session)
    db.flush()
    record(db, mentorship, current_user, "session_scheduled", f"Session scheduled: {session.title}",
           entity_type="session", entity_id=session.id)
    notify_other(db, mentorship, current_user, "session_scheduled", "New mentoring session",
                 f"{current_user.full_name} scheduled \"{session.title}\".")
    db.commit()
    db.refresh(session)
    return session_dict(session)


@router.get("/{mentorship_id}/sessions/{session_id}")
def get_session(
    mentorship_id: int,
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user)
    session = get_session_or_404(db, mentorship, session_id)
    notes = (
        visible_notes_query(db, mentorship, current_user)
        .filter(SessionNote.session_id == session.id).order_by(SessionNote.created_at.asc()).all()
    )
    items = db.query(ActionItem).filter(ActionItem.session_id == session.id).order_by(ActionItem.id.asc()).all()
    return {
        **session_dict(session),
        "participants": [party_dict(db, mentorship.mentor_id, "mentor"), party_dict(db, mentorship.mentee_id, "mentee")],
        "is_writable": mentorship.status == "accepted",
        "notes": [note_dict(db, note, current_user, session.title) for note in notes],
        "action_items": [action_dict(db, item) for item in items],
    }


@router.patch("/{mentorship_id}/sessions/{session_id}")
def update_session(
    mentorship_id: int,
    session_id: int,
    data: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user, writable=True)
    session = get_session_or_404(db, mentorship, session_id)
    if session.status != "scheduled":
        raise HTTPException(status.HTTP_409_CONFLICT, f"A {session.status} session can no longer be edited.")

    changes = data.model_dump(exclude_unset=True)
    if session.booking_id is not None and ({"scheduled_at", "duration_minutes"} & changes.keys()):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This session comes from a booked time slot. Cancel it and book another slot to change the time.",
        )
    for field, value in changes.items():
        if value is None and field in ("title", "scheduled_at", "duration_minutes", "meeting_type"):
            continue
        setattr(session, field, value if value != "" else None)
    if session.meeting_type == "virtual":
        session.location = None
    else:
        session.meeting_link = None
    record(db, mentorship, current_user, "session_updated", f"Session updated: {session.title}",
           entity_type="session", entity_id=session.id)
    db.commit()
    db.refresh(session)
    return session_dict(session)


def release_booking(db: Session, session: MentorshipSession) -> None:
    """Cancelling a booked session frees its availability slot, as cancelling the booking does."""
    if session.booking_id is None:
        return
    booking = db.get(Booking, session.booking_id)
    if booking is not None and booking.status == "confirmed":
        booking.status = "cancelled"
        slot = db.get(MentorAvailability, booking.availability_id)
        if slot is not None:
            slot.status = "available"


@router.post("/{mentorship_id}/sessions/{session_id}/cancel")
def cancel_session(
    mentorship_id: int,
    session_id: int,
    data: SessionCancel | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user, writable=True)
    session = get_session_or_404(db, mentorship, session_id)
    if session.status != "scheduled":
        raise HTTPException(status.HTTP_409_CONFLICT, "Only a scheduled session can be cancelled.")
    if session.booking_id is not None and as_utc(session.scheduled_at) <= now_utc():
        raise HTTPException(status.HTTP_409_CONFLICT, "A session that has already started cannot be cancelled.")
    session.status = "cancelled"
    session.cancel_reason = (data.reason if data else None) or None
    release_booking(db, session)
    record(db, mentorship, current_user, "session_cancelled", f"Session cancelled: {session.title}",
           entity_type="session", entity_id=session.id, old_value="scheduled", new_value="cancelled")
    notify_other(db, mentorship, current_user, "session_cancelled", "Mentoring session cancelled",
                 f"{current_user.full_name} cancelled \"{session.title}\".")
    db.commit()
    db.refresh(session)
    return session_dict(session)


@router.post("/{mentorship_id}/sessions/{session_id}/complete")
def complete_session(
    mentorship_id: int,
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user, writable=True)
    session = get_session_or_404(db, mentorship, session_id)
    if session.status != "scheduled":
        raise HTTPException(status.HTTP_409_CONFLICT, "Only a scheduled session can be marked as completed.")
    if as_utc(session.scheduled_at) > now_utc():
        raise HTTPException(status.HTTP_409_CONFLICT, "A session can be marked as completed once it has started.")
    session.status = "completed"
    record(db, mentorship, current_user, "session_completed", f"Session completed: {session.title}",
           entity_type="session", entity_id=session.id, old_value="scheduled", new_value="completed")
    db.commit()
    db.refresh(session)
    return session_dict(session)


# ---------------------------------------------------------------- meeting notes

@router.get("/{mentorship_id}/notes")
def list_notes(
    mentorship_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user)
    rows = (
        visible_notes_query(db, mentorship, current_user)
        .order_by(SessionNote.created_at.desc()).all()
    )
    titles = {s.id: s.title for s in db.query(MentorshipSession).filter(MentorshipSession.mentorship_id == mentorship.id)}
    return [note_dict(db, note, current_user, titles.get(note.session_id)) for note in rows]


@router.post("/{mentorship_id}/sessions/{session_id}/notes", status_code=status.HTTP_201_CREATED)
def create_note(
    mentorship_id: int,
    session_id: int,
    data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user, writable=True)
    session = get_session_or_404(db, mentorship, session_id)
    if session.status == "cancelled":
        raise HTTPException(status.HTTP_409_CONFLICT, "Notes cannot be added to a cancelled session.")
    note = SessionNote(
        session_id=session.id, mentorship_id=mentorship.id, author_id=current_user.id, visibility=data.visibility,
        **{name: (getattr(data, name) or None) for name in NOTE_FIELDS},
    )
    db.add(note)
    db.flush()
    if note.visibility == "shared":  # a private note leaves no trace for the other participant
        record(db, mentorship, current_user, "note_shared", f"Shared meeting notes added: {session.title}",
               entity_type="session", entity_id=session.id)
    db.commit()
    db.refresh(note)
    return note_dict(db, note, current_user, session.title)


@router.patch("/{mentorship_id}/notes/{note_id}")
def update_note(
    mentorship_id: int,
    note_id: int,
    data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user, writable=True)
    note = visible_notes_query(db, mentorship, current_user).filter(SessionNote.id == note_id).first()
    if note is None:  # missing, or someone else's private note: indistinguishable on purpose
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Note not found.")
    if note.author_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the author can edit this note.")
    changes = data.model_dump(exclude_unset=True)
    was_private = note.visibility == "private"
    for field, value in changes.items():
        if field == "visibility" and value is None:
            continue
        setattr(note, field, (value or None) if field in NOTE_FIELDS else value)
    if not any(getattr(note, name) for name in NOTE_FIELDS):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A note needs at least one section with content.")
    if was_private and note.visibility == "shared":
        session = db.get(MentorshipSession, note.session_id)
        record(db, mentorship, current_user, "note_shared", f"Shared meeting notes added: {session.title}",
               entity_type="session", entity_id=note.session_id)
    db.commit()
    db.refresh(note)
    session = db.get(MentorshipSession, note.session_id)
    return note_dict(db, note, current_user, session.title if session else None)


# ---------------------------------------------------------------- goals

def get_goal_or_404(db: Session, mentorship: Mentorship, goal_id: int) -> MentorshipGoal:
    goal = db.query(MentorshipGoal).filter(
        MentorshipGoal.id == goal_id, MentorshipGoal.mentorship_id == mentorship.id
    ).first()
    if goal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Goal not found.")
    return goal


@router.get("/{mentorship_id}/goals")
def list_goals(
    mentorship_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user)
    goals = (
        db.query(MentorshipGoal).filter(MentorshipGoal.mentorship_id == mentorship.id)
        .order_by(MentorshipGoal.created_at.desc()).all()
    )
    return [goal_dict(db, goal) for goal in goals]


@router.post("/{mentorship_id}/goals", status_code=status.HTTP_201_CREATED)
def create_goal(
    mentorship_id: int,
    data: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user, writable=True)
    check_participant(mentorship, data.assignee_id, "The person responsible")
    goal = MentorshipGoal(
        mentorship_id=mentorship.id, created_by_id=current_user.id, title=data.title,
        description=data.description or None, target_date=data.target_date,
        assignee_id=data.assignee_id, status=data.status,
        completed_at=now_utc() if data.status == "completed" else None,
    )
    db.add(goal)
    db.flush()
    record(db, mentorship, current_user, "goal_created", f"Goal created: {goal.title}",
           entity_type="goal", entity_id=goal.id, new_value=goal.status)
    notify_other(db, mentorship, current_user, "goal_created", "New mentorship goal",
                 f"{current_user.full_name} added the goal \"{goal.title}\".")
    db.commit()
    db.refresh(goal)
    return goal_dict(db, goal)


@router.patch("/{mentorship_id}/goals/{goal_id}")
def update_goal(
    mentorship_id: int,
    goal_id: int,
    data: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user, writable=True)
    goal = get_goal_or_404(db, mentorship, goal_id)
    changes = data.model_dump(exclude_unset=True)
    check_participant(mentorship, changes.get("assignee_id"), "The person responsible")

    edited = False
    for field in ("title", "description", "target_date", "assignee_id"):
        if field in changes and changes[field] is not None and changes[field] != getattr(goal, field):
            setattr(goal, field, changes[field] or None)
            edited = True
    if changes.get("clear_target_date") and goal.target_date is not None:
        goal.target_date, edited = None, True
    if changes.get("clear_assignee") and goal.assignee_id is not None:
        goal.assignee_id, edited = None, True

    new_status = changes.get("status")
    if new_status and new_status != goal.status:
        old = goal.status
        goal.status = new_status
        goal.completed_at = now_utc() if new_status == "completed" else None
        record(
            db, mentorship, current_user,
            "goal_completed" if new_status == "completed" else "goal_status_changed",
            f"Goal {'completed' if new_status == 'completed' else 'moved to ' + new_status.replace('_', ' ')}: {goal.title}",
            entity_type="goal", entity_id=goal.id, old_value=old, new_value=new_status,
        )
    if edited:
        record(db, mentorship, current_user, "goal_updated", f"Goal updated: {goal.title}",
               entity_type="goal", entity_id=goal.id)
    db.commit()
    db.refresh(goal)
    return goal_dict(db, goal)


@router.get("/{mentorship_id}/goals/{goal_id}/history")
def goal_history(
    mentorship_id: int,
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user)
    goal = get_goal_or_404(db, mentorship, goal_id)
    events = (
        db.query(MentorshipActivityEvent)
        .filter(MentorshipActivityEvent.mentorship_id == mentorship.id,
                MentorshipActivityEvent.entity_type == "goal", MentorshipActivityEvent.entity_id == goal.id)
        .order_by(MentorshipActivityEvent.created_at.desc(), MentorshipActivityEvent.id.desc()).all()
    )
    return [event_dict(db, event) for event in events]


# ---------------------------------------------------------------- action items

@router.get("/{mentorship_id}/action-items")
def list_action_items(
    mentorship_id: int,
    state: Literal["open", "completed", "all"] = Query(default="all"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user)
    query = db.query(ActionItem).filter(ActionItem.mentorship_id == mentorship.id)
    if state != "all":
        query = query.filter(ActionItem.status == state)
    return [action_dict(db, item) for item in query.order_by(ActionItem.status.desc(), ActionItem.due_date.asc(), ActionItem.id.asc()).all()]


@router.post("/{mentorship_id}/action-items", status_code=status.HTTP_201_CREATED)
def create_action_item(
    mentorship_id: int,
    data: ActionItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user, writable=True)
    check_participant(mentorship, data.assigned_to_id, "The person responsible")
    check_goal_and_session(db, mentorship, data.goal_id, data.session_id)
    item = ActionItem(
        mentorship_id=mentorship.id, created_by_id=current_user.id, assigned_to_id=data.assigned_to_id,
        description=data.description, due_date=data.due_date, goal_id=data.goal_id, session_id=data.session_id,
    )
    db.add(item)
    db.flush()
    record(db, mentorship, current_user, "action_item_created", f"Action item created: {item.description}",
           entity_type="action_item", entity_id=item.id)
    if item.assigned_to_id != current_user.id:
        notify_other(db, mentorship, current_user, "action_item_assigned", "New action item for you",
                     f"{current_user.full_name} assigned you: {item.description}")
    db.commit()
    db.refresh(item)
    return action_dict(db, item)


@router.patch("/{mentorship_id}/action-items/{item_id}")
def update_action_item(
    mentorship_id: int,
    item_id: int,
    data: ActionItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user, writable=True)
    item = db.query(ActionItem).filter(ActionItem.id == item_id, ActionItem.mentorship_id == mentorship.id).first()
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Action item not found.")
    changes = data.model_dump(exclude_unset=True)
    check_participant(mentorship, changes.get("assigned_to_id"), "The person responsible")
    check_goal_and_session(db, mentorship, changes.get("goal_id"), changes.get("session_id"))

    for field in ("description", "assigned_to_id", "due_date", "goal_id", "session_id"):
        if changes.get(field) is not None:
            setattr(item, field, changes[field])
    if changes.get("clear_due_date"):
        item.due_date = None
    if changes.get("clear_goal"):
        item.goal_id = None

    new_status = changes.get("status")
    if new_status and new_status != item.status:
        item.status = new_status
        if new_status == "completed":
            item.completed_at = now_utc()
            record(db, mentorship, current_user, "action_item_completed", f"Action item completed: {item.description}",
                   entity_type="action_item", entity_id=item.id, old_value="open", new_value="completed")
        else:
            item.completed_at = None
            record(db, mentorship, current_user, "action_item_reopened", f"Action item reopened: {item.description}",
                   entity_type="action_item", entity_id=item.id, old_value="completed", new_value="open")
    db.commit()
    db.refresh(item)
    return action_dict(db, item)


# ---------------------------------------------------------------- progress, timeline, closure

@router.get("/{mentorship_id}/progress")
def get_progress(
    mentorship_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user)
    goals = (
        db.query(MentorshipGoal).filter(MentorshipGoal.mentorship_id == mentorship.id)
        .order_by(MentorshipGoal.created_at.asc()).all()
    )
    completed_items = (
        db.query(ActionItem)
        .filter(ActionItem.mentorship_id == mentorship.id, ActionItem.status == "completed")
        .order_by(ActionItem.completed_at.desc()).all()
    )
    sessions = (
        db.query(MentorshipSession)
        .filter(MentorshipSession.mentorship_id == mentorship.id, MentorshipSession.status == "completed")
        .order_by(MentorshipSession.scheduled_at.desc()).all()
    )
    return {
        **compute_progress(db, mentorship),
        "goal_list": [goal_dict(db, goal) for goal in goals],
        "completed_action_items": [action_dict(db, item) for item in completed_items],
        "completed_sessions": [session_dict(s) for s in sessions],
    }


@router.get("/{mentorship_id}/timeline")
def get_timeline(
    mentorship_id: int,
    order: Literal["asc", "desc"] = Query(default="desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user)
    events = timeline_events(db, mentorship)
    return events if order == "asc" else events[::-1]


@router.post("/{mentorship_id}/close")
def close_mentorship(
    mentorship_id: int,
    data: CloseMentorship | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user, writable=True)
    now = now_utc()
    mentorship.status = "completed"
    mentorship.closed_at = now
    mentorship.closed_by_id = current_user.id
    mentorship.outcome_summary = (data.outcome_summary if data else None) or None

    # Sessions that have not happened yet can no longer take place. They are cancelled, not deleted.
    for session in db.query(MentorshipSession).filter(
        MentorshipSession.mentorship_id == mentorship.id, MentorshipSession.status == "scheduled"
    ).all():
        if as_utc(session.scheduled_at) > now:
            session.status = "cancelled"
            session.cancel_reason = "Mentorship closed"
            release_booking(db, session)

    notify_other(db, mentorship, current_user, "mentorship_completed", "Mentorship completed",
                 f"{current_user.full_name} marked your mentorship as completed.")
    db.commit()
    db.refresh(mentorship)
    return {
        "id": mentorship.id, "status": mentorship.status,
        "closed_at": as_utc(mentorship.closed_at), "outcome_summary": mentorship.outcome_summary,
    }


# ---------------------------------------------------------------- match feedback

@router.get("/{mentorship_id}/feedback")
def get_feedback(
    mentorship_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user)
    mine = db.query(MentorshipFeedback).filter(
        MentorshipFeedback.mentorship_id == mentorship.id, MentorshipFeedback.user_id == current_user.id
    ).first()
    return {
        "can_submit": mentorship.status == "completed" and mine is None,
        "mine": {"rating": mine.rating, "comment": mine.comment, "created_at": as_utc(mine.created_at)} if mine else None,
    }


@router.post("/{mentorship_id}/feedback", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    mentorship_id: int,
    data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentorship = load_mentorship(db, mentorship_id, current_user)
    if mentorship.status != "completed":
        raise HTTPException(status.HTTP_409_CONFLICT, "Feedback can be given once the mentorship is completed.")
    if db.query(MentorshipFeedback.id).filter(
        MentorshipFeedback.mentorship_id == mentorship.id, MentorshipFeedback.user_id == current_user.id
    ).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "You have already given feedback for this mentorship.")
    feedback = MentorshipFeedback(
        mentorship_id=mentorship.id, user_id=current_user.id, rating=data.rating, comment=data.comment or None,
    )
    db.add(feedback)
    db.commit()
    return {"rating": feedback.rating, "comment": feedback.comment, "created_at": as_utc(feedback.created_at)}
