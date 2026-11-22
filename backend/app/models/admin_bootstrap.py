from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.database.database import Base


class AdminBootstrapAudit(Base):
    __tablename__ = "admin_bootstrap_audit"

    id = Column(Integer, primary_key=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    target_email = Column(String(255), nullable=False)
    actor = Column(String(80), nullable=False, default="local-cli")
    action = Column(String(40), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
