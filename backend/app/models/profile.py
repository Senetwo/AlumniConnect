
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True
    )

    career_domain = Column(String(100), nullable=False)
    career_path = Column(String(100), nullable=False)
    experience = Column(String(50), nullable=False)
    skills = Column(Text, nullable=False)
    certifications = Column(Text, nullable=True)
    career_goals = Column(Text, nullable=False)
    mentorship_interests = Column(Text, nullable=True)
    availability = Column(String(100), nullable=False)
    bio = Column(Text, nullable=True)

    profile_picture_url = Column(String(1000), nullable=True)
    directory_visible = Column(Boolean, nullable=False, default=False)

    user = relationship(
        "User",
        back_populates="profile"
    )
