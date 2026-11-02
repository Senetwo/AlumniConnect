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
    role: str = Field(pattern="^(mentor|mentee)$")
    profile: ProfileRegistration


class ClerkOnboarding(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    role: str = Field(pattern="^(mentor|mentee)$")
    profile: ProfileRegistration


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginResponse(BaseModel):
    """Either a finished sign-in, or a request for the emailed one-time code."""
    access_token: str | None = None
    token_type: str | None = None
    mfa_required: bool = False
    challenge_token: str | None = None
    email_hint: str | None = None
    email_sent: bool | None = None


class OtpVerifyRequest(BaseModel):
    challenge_token: str = Field(min_length=20, max_length=200)
    code: str = Field(min_length=6, max_length=6, pattern=r"^[0-9]{6}$")


class OtpResendRequest(BaseModel):
    challenge_token: str = Field(min_length=20, max_length=200)


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    is_email_verified: bool = True
    verification_email_sent: bool | None = None

    model_config = {
        "from_attributes": True
    }


class EmailVerificationRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)


class EmailAddressRequest(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    new_password: str = Field(min_length=8, max_length=128)
