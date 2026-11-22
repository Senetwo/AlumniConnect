
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


AvailabilityStatus = Literal["available", "booked", "cancelled"]
BookingStatus = Literal["confirmed", "cancelled"]


class AvailabilityCreate(BaseModel):
    start_at: datetime
    end_at: datetime

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_at.tzinfo is None or self.start_at.utcoffset() is None:
            raise ValueError("start_at must include a timezone.")

        if self.end_at.tzinfo is None or self.end_at.utcoffset() is None:
            raise ValueError("end_at must include a timezone.")

        if self.end_at <= self.start_at:
            raise ValueError("end_at must be later than start_at.")

        return self


class AvailabilityResponse(BaseModel):
    id: int
    mentor_id: int
    start_at: datetime
    end_at: datetime
    status: AvailabilityStatus

    model_config = ConfigDict(from_attributes=True)


class BookingCreate(BaseModel):
    mentorship_id: int = Field(gt=0)
    availability_id: int = Field(gt=0)


class BookingResponse(BaseModel):
    id: int
    availability_id: int
    mentorship_id: int
    mentee_id: int
    status: BookingStatus
    created_at: datetime
    start_at: datetime | None = None
    end_at: datetime | None = None
    mentor_name: str | None = None
    mentee_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
