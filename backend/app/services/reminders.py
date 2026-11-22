"""Reminders created on demand, so no background scheduler is needed.

Called when a member's notifications (or the bell count) are read. Each reminder is created
once per (member, kind, item); reading again never duplicates it.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.mentorship import Mentorship
from app.models.notifications import Notification
from app.models.workspace import ActionItem, MentorshipSession
from app.services.notification_service import create_notification

EAT = timezone(timedelta(hours=3))
SESSION_WINDOW = timedelta(hours=24)


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _already_sent(db: Session, user_id: int, kind: str, resource_id: int) -> bool:
    return db.query(Notification.id).filter(
        Notification.user_id == user_id, Notification.type == kind, Notification.resource_id == resource_id
    ).first() is not None


def generate_reminders(db: Session, user) -> int:
    now = datetime.now(timezone.utc)
    today = datetime.now(EAT).date()
    created = 0

    active_ids = [
        mentorship_id for (mentorship_id,) in db.query(Mentorship.id).filter(
            Mentorship.status == "accepted", or_(Mentorship.mentor_id == user.id, Mentorship.mentee_id == user.id)
        )
    ]
    if not active_ids:
        return 0

    for session in db.query(MentorshipSession).filter(
        MentorshipSession.mentorship_id.in_(active_ids), MentorshipSession.status == "scheduled"
    ):
        start = _aware(session.scheduled_at)
        if now <= start <= now + SESSION_WINDOW and not _already_sent(db, user.id, "session_reminder", session.id):
            when = start.astimezone(EAT).strftime("%a %d %b, %H:%M")
            create_notification(
                db, user_id=user.id, notification_type="session_reminder", title="Session coming up",
                message=f"\"{session.title}\" starts {when} EAT.", resource_type="session", resource_id=session.id,
            )
            created += 1

    for item in db.query(ActionItem).filter(
        ActionItem.mentorship_id.in_(active_ids), ActionItem.assigned_to_id == user.id,
        ActionItem.status == "open", ActionItem.due_date.isnot(None), ActionItem.due_date < today,
    ):
        if not _already_sent(db, user.id, "action_item_overdue", item.id):
            create_notification(
                db, user_id=user.id, notification_type="action_item_overdue", title="Action item overdue",
                message=f"Overdue since {item.due_date.strftime('%d %b')}: {item.description}",
                resource_type="action_item", resource_id=item.id,
            )
            created += 1

    if created:
        db.commit()
    return created
