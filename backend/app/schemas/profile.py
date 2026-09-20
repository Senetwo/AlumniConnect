from pydantic import BaseModel, field_validator


class ProfileCreate(BaseModel):
    role: str
    career_domain: str
    career_path: str
    experience: str
    skills: list[str]
    career_goals: str
    availability: str


class ProfileResponse(ProfileCreate):
    id: int

    @field_validator("skills", mode="before")
    @classmethod
    def parse_skills(cls, value):
        if isinstance(value, str):
            return [
                skill.strip()
                for skill in value.split(",")
                if skill.strip()
            ]

        return value

    model_config = {
        "from_attributes": True
    }