from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.database.database import Base


def _now():
    return datetime.now(timezone.utc)


class CommunityPost(Base):
    __tablename__ = "community_posts"

    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now, index=True)


class CommunityPostLike(Base):
    __tablename__ = "community_post_likes"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_post_like"),)

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)


class CommunityEvent(Base):
    __tablename__ = "community_events"

    id = Column(Integer, primary_key=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(160), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(200), nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    link = Column(String(500), nullable=True)
    is_cancelled = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)


class CommunityEventRsvp(Base):
    __tablename__ = "community_event_rsvps"
    __table_args__ = (UniqueConstraint("event_id", "user_id", name="uq_event_rsvp"),)

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("community_events.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)


class JobOpportunity(Base):
    __tablename__ = "job_opportunities"

    id = Column(Integer, primary_key=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(160), nullable=False)
    company = Column(String(160), nullable=False, default="Kenya Airways")
    location = Column(String(200), nullable=False)
    employment_type = Column(String(30), nullable=False)
    description = Column(Text, nullable=False)
    apply_url = Column(String(500), nullable=True)
    contact_email = Column(String(255), nullable=True)
    closes_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now, index=True)
