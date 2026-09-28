from pydantic import BaseModel, EmailStr, Field


class ProfileRegistration(BaseModel):
    career_domain: str
    career_path: str
    experience: str
    skills: list[str]
    certifications: list[str] = []
    career_goals: str
    mentorship_interests: list[str] = []
    availability: str
    bio: str | None = None


class UserRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(pattern="^(mentor|mentee|admin)$")
    profile: ProfileRegistration


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str

    model_config = {
        "from_attributes": True
    }