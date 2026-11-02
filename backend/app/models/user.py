from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, text
from sqlalchemy.orm import relationship

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    # Additive external identity mapping; existing local accounts remain intact.
    clerk_user_id = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    # Keeps a member's community permissions when their administrative role changes.
    community_role = Column(String(20), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    # Existing accounts are treated as verified by the startup migration;
    # newly registered accounts explicitly set this to False.
    is_email_verified = Column(Boolean, nullable=False, default=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    profile = relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
