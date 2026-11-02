
from pydantic import BaseModel, Field, field_validator, HttpUrl


class ProfileCreate(BaseModel):
    user_id: int
    career_domain: str
    career_path: str
    experience: str
    skills: list[str]
    certifications: list[str] = Field(default_factory=list)
    career_goals: str
    mentorship_interests: list[str] = Field(default_factory=list)
    availability: str
    bio: str | None = None
    profile_picture_url: HttpUrl | None = None


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    career_domain: str
    career_path: str
    experience: str
    skills: list[str]
    certifications: list[str]
    career_goals: str
    mentorship_interests: list[str]
    availability: str
    bio: str | None
    profile_picture_url: str | None = None
    directory_visible: bool = False

    @field_validator(
        "skills",
        "certifications",
        "mentorship_interests",
        mode="before",
    )
    @classmethod
    def parse_list_fields(cls, value):
        if isinstance(value, str):
            return [
                item.strip()
                for item in value.split(",")
                if item.strip()
            ]
        return value

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    career_domain: str
    career_path: str
    experience: str
    skills: list[str]
    certifications: list[str] = Field(default_factory=list)
    career_goals: str
    mentorship_interests: list[str] = Field(default_factory=list)
    availability: str
    bio: str | None = None
    profile_picture_url: HttpUrl | None = None
    directory_visible: bool = False
