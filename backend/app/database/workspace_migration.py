"""Schema changes for the mentorship workspace.

Everything here is additive and safe to run on every start:
  * new tables come from Base.metadata.create_all (called before this runs);
  * three nullable columns are added to mentorships when missing;
  * the mentorships status CHECK is widened to allow 'completed' (PostgreSQL only;
    no rows change);
  * each existing booking gets a linked mentorship session when it has none.
No data is deleted or rewritten.
"""
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.models.booking import Booking, MentorAvailability
from app.models.mentorship import Mentorship
from app.models.workspace import MentorshipActivityEvent, MentorshipSession

SESSION_FROM_BOOKING_TITLE = "Mentoring session"


def apply_workspace_migration(engine) -> None:
    inspector = inspect(engine)
    if inspector.has_table("mentorships"):
        existing = {column["name"] for column in inspector.get_columns("mentorships")}
        with engine.begin() as connection:
            for name, declaration in (
                ("closed_at", "TIMESTAMP WITH TIME ZONE"),
                ("closed_by_id", "INTEGER REFERENCES users(id)"),
                ("outcome_summary", "TEXT"),
            ):
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE mentorships ADD COLUMN {name} {declaration}"))

            if engine.dialect.name == "postgresql":
                definition = connection.execute(text(
                    "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                    "WHERE conname = 'check_mentorship_status' AND conrelid = 'mentorships'::regclass"
                )).scalar()
                if definition is not None and "completed" not in definition:
                    connection.execute(text("ALTER TABLE mentorships DROP CONSTRAINT check_mentorship_status"))
                    connection.execute(text(
                        "ALTER TABLE mentorships ADD CONSTRAINT check_mentorship_status "
                        "CHECK (status IN ('pending', 'accepted', 'declined', 'completed'))"
                    ))

    with Session(engine) as db:
        backfill_sessions_from_bookings(db)


def backfill_sessions_from_bookings(db: Session) -> int:
    """Create a mentorship session for every booking that does not have one yet."""
    linked = {booking_id for (booking_id,) in db.query(MentorshipSession.booking_id).filter(
        MentorshipSession.booking_id.isnot(None)
    )}
    rows = (
        db.query(Booking, MentorAvailability)
        .join(MentorAvailability, MentorAvailability.id == Booking.availability_id)
        .all()
    )
    created = 0
    for booking, slot in rows:
        if booking.id in linked:
            continue
        minutes = max(5, min(480, int((slot.end_at - slot.start_at).total_seconds() // 60)))
        cancelled = booking.status != "confirmed"
        session = MentorshipSession(
            mentorship_id=booking.mentorship_id,
            created_by_id=booking.mentee_id,
            booking_id=booking.id,
            title=SESSION_FROM_BOOKING_TITLE,
            scheduled_at=slot.start_at,
            duration_minutes=minutes,
            meeting_type="virtual",
            status="cancelled" if cancelled else "scheduled",
            created_at=booking.created_at,
            updated_at=booking.created_at,
        )
        db.add(session)
        db.flush()
        db.add(MentorshipActivityEvent(
            mentorship_id=booking.mentorship_id,
            actor_id=booking.mentee_id,
            event_type="session_scheduled",
            entity_type="session",
            entity_id=session.id,
            summary=f"Session scheduled: {SESSION_FROM_BOOKING_TITLE}",
            created_at=booking.created_at,
        ))
        created += 1
    db.commit()
    return created
