
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


MentorshipStatus = Literal["pending", "accepted", "declined", "completed"]
MentorshipDecision = Literal["accepted", "declined"]


class MentorshipRequestCreate(BaseModel):
    mentor_id: int = Field(gt=0)
    motivation: str = Field(
        min_length=20,
        max_length=1000,
        description="Why the mentee wants this mentor and what they hope to achieve.",
    )


class MentorshipDecisionRequest(BaseModel):
    decision: MentorshipDecision


class MentorshipResponse(BaseModel):
    id: int
    mentee_id: int
    mentor_id: int
    mentee_name: str
    mentor_name: str
    motivation: str
    status: MentorshipStatus
    created_at: datetime
    responded_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
