
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String, Text

from app.database.database import Base


class KnowledgeResource(Base):
    __tablename__ = "knowledge_resources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)
    url = Column(String(1000), nullable=False)
    source_name = Column(String(200), nullable=True)
    source_author = Column(String(200), nullable=True)
    publication_date = Column(Date, nullable=True)
    is_published = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
