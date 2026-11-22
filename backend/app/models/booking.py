
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)

from app.database.database import Base


class MentorAvailability(Base):
    __tablename__ = "mentor_availability"

    id = Column(Integer, primary_key=True, index=True)

    mentor_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="available",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        CheckConstraint(
            "end_at > start_at",
            name="check_availability_end_after_start",
        ),
        CheckConstraint(
            "status IN ('available', 'booked', 'cancelled')",
            name="check_availability_status",
        ),
        Index("ix_availability_mentor_start", "mentor_id", "start_at"),
    )


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    availability_id = Column(
        Integer,
        ForeignKey("mentor_availability.id"),
        nullable=False,
        unique=True,
    )

    mentorship_id = Column(
        Integer,
        ForeignKey("mentorships.id"),
        nullable=False,
        index=True,
    )

    mentee_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    status = Column(
        String(20),
        nullable=False,
        default="confirmed",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('confirmed', 'cancelled')",
            name="check_booking_status",
        ),
    )
