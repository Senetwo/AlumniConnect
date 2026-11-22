"""Mentorship workspace records. Every row hangs off an existing mentorships row."""
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.database.database import Base


def _now():
    return datetime.now(timezone.utc)


class MentorshipSession(Base):
    __tablename__ = "mentorship_sessions"

    id = Column(Integer, primary_key=True, index=True)
    mentorship_id = Column(Integer, ForeignKey("mentorships.id"), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Set when the session came from a booked availability slot, so a booking and its
    # session are one record seen from two places.
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True, unique=True)

    title = Column(String(160), nullable=False)
    description = Column(Text, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=60)
    meeting_type = Column(String(20), nullable=False, default="virtual")
    location = Column(String(255), nullable=True)
    meeting_link = Column(String(1000), nullable=True)
    agenda = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="scheduled")
    cancel_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("status IN ('scheduled', 'completed', 'cancelled')", name="check_session_status"),
        CheckConstraint("meeting_type IN ('virtual', 'in_person')", name="check_session_meeting_type"),
        CheckConstraint("duration_minutes BETWEEN 5 AND 480", name="check_session_duration"),
        Index("ix_session_mentorship_time", "mentorship_id", "scheduled_at"),
    )


class SessionNote(Base):
    __tablename__ = "session_notes"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("mentorship_sessions.id"), nullable=False, index=True)
    mentorship_id = Column(Integer, ForeignKey("mentorships.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # 'shared' notes are visible to both participants, 'private' only to the author.
    visibility = Column(String(10), nullable=False)

    topics_discussed = Column(Text, nullable=True)
    key_takeaways = Column(Text, nullable=True)
    challenges = Column(Text, nullable=True)
    advice = Column(Text, nullable=True)
    decisions = Column(Text, nullable=True)
    next_steps = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        CheckConstraint("visibility IN ('shared', 'private')", name="check_note_visibility"),
    )


class MentorshipGoal(Base):
    __tablename__ = "mentorship_goals"

    id = Column(Integer, primary_key=True, index=True)
    mentorship_id = Column(Integer, ForeignKey("mentorships.id"), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # NULL means the goal is shared by both participants.
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    title = Column(String(160), nullable=False)
    description = Column(Text, nullable=True)
    target_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default="not_started")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed', 'on_hold')",
            name="check_goal_status",
        ),
    )


class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, index=True)
    mentorship_id = Column(Integer, ForeignKey("mentorships.id"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("mentorship_sessions.id"), nullable=True, index=True)
    goal_id = Column(Integer, ForeignKey("mentorship_goals.id"), nullable=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    description = Column(String(500), nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default="open")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('open', 'completed')", name="check_action_item_status"),
    )


class MentorshipFeedback(Base):
    """One rating per participant, given after a mentorship is completed.

    Only the author and administrators (as an aggregate) can see it; the other participant
    cannot.
    """

    __tablename__ = "mentorship_feedback"

    id = Column(Integer, primary_key=True, index=True)
    mentorship_id = Column(Integer, ForeignKey("mentorships.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="check_feedback_rating"),
        UniqueConstraint("mentorship_id", "user_id", name="uq_feedback_once"),
    )


class MentorshipActivityEvent(Base):
    """Something that actually happened. Never holds private note content."""

    __tablename__ = "mentorship_activity_events"

    id = Column(Integer, primary_key=True, index=True)
    mentorship_id = Column(Integer, ForeignKey("mentorships.id"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_type = Column(String(40), nullable=False)
    entity_type = Column(String(20), nullable=True)
    entity_id = Column(Integer, nullable=True)
    summary = Column(String(300), nullable=False)
    old_value = Column(String(40), nullable=True)
    new_value = Column(String(40), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        Index("ix_activity_mentorship_time", "mentorship_id", "created_at"),
        Index("ix_activity_entity", "entity_type", "entity_id"),
    )
