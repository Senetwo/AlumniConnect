from pydantic import BaseModel, field_validator


class ProfileCreate(BaseModel):
    user_id: int
    career_domain: str
    career_path: str
    experience: str
    skills: list[str]
    certifications: list[str] = []
    career_goals: str
    mentorship_interests: list[str] = []
    availability: str
    bio: str | None = None


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

    @field_validator(
        "skills",
        "certifications",
        "mentorship_interests",
        mode="before"
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

    model_config = {
        "from_attributes": True
    }