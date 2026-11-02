
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.database import Base


class Mentorship(Base):
    __tablename__ = "mentorships"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'accepted', 'declined')",
            name="check_mentorship_status",
        ),
        Index(
            "uq_active_mentorship_pair",
            "mentee_id",
            "mentor_id",
            unique=True,
            postgresql_where=Column("status").in_(["pending", "accepted"]),
            sqlite_where=Column("status").in_(["pending", "accepted"]),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    mentee_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    mentor_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    motivation = Column(Text, nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="pending",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    responded_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    mentee = relationship("User", foreign_keys=[mentee_id])
    mentor = relationship("User", foreign_keys=[mentor_id])

    @property
    def mentee_name(self) -> str:
        return self.mentee.full_name

    @property
    def mentor_name(self) -> str:
        return self.mentor.full_name
