from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

MeetingType = Literal["virtual", "in_person"]
GoalStatus = Literal["not_started", "in_progress", "completed", "on_hold"]
ActionItemStatus = Literal["open", "completed"]
NoteVisibility = Literal["shared", "private"]


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Include a time zone offset, for example 2026-11-10T10:00:00+03:00.")
    return value.astimezone(timezone.utc)


class _Text(BaseModel):
    """Trims every string field and turns blanks into None."""

    @field_validator("*", mode="before")
    @classmethod
    def _trim(cls, value):
        return value.strip() if isinstance(value, str) else value


def _check_link(value: str | None) -> str | None:
    value = _clean(value)
    if value and not value.lower().startswith(("http://", "https://")):
        raise ValueError("Meeting link must start with http:// or https://.")
    return value


class SessionCreate(_Text):
    title: str = Field(min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=5, le=480)
    meeting_type: MeetingType = "virtual"
    location: str | None = Field(default=None, max_length=255)
    meeting_link: str | None = Field(default=None, max_length=1000)
    agenda: str | None = Field(default=None, max_length=4000)

    _tz = field_validator("scheduled_at")(lambda cls, v: _aware(v))
    _link = field_validator("meeting_link")(lambda cls, v: _check_link(v))


class SessionUpdate(_Text):
    title: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=5, le=480)
    meeting_type: MeetingType | None = None
    location: str | None = Field(default=None, max_length=255)
    meeting_link: str | None = Field(default=None, max_length=1000)
    agenda: str | None = Field(default=None, max_length=4000)

    @field_validator("scheduled_at")
    @classmethod
    def _tz(cls, value):
        return _aware(value) if value is not None else value

    _link = field_validator("meeting_link")(lambda cls, v: _check_link(v))


class SessionCancel(_Text):
    reason: str | None = Field(default=None, max_length=500)


NOTE_FIELDS = ("topics_discussed", "key_takeaways", "challenges", "advice", "decisions", "next_steps")


class NoteCreate(_Text):
    # No default: the author must pick shared or private on every note.
    visibility: NoteVisibility
    topics_discussed: str | None = Field(default=None, max_length=4000)
    key_takeaways: str | None = Field(default=None, max_length=4000)
    challenges: str | None = Field(default=None, max_length=4000)
    advice: str | None = Field(default=None, max_length=4000)
    decisions: str | None = Field(default=None, max_length=4000)
    next_steps: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def _not_empty(self):
        if not any(_clean(getattr(self, name)) for name in NOTE_FIELDS):
            raise ValueError("Write something in at least one section.")
        return self


class NoteUpdate(_Text):
    visibility: NoteVisibility | None = None
    topics_discussed: str | None = Field(default=None, max_length=4000)
    key_takeaways: str | None = Field(default=None, max_length=4000)
    challenges: str | None = Field(default=None, max_length=4000)
    advice: str | None = Field(default=None, max_length=4000)
    decisions: str | None = Field(default=None, max_length=4000)
    next_steps: str | None = Field(default=None, max_length=4000)


class GoalCreate(_Text):
    title: str = Field(min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    target_date: date | None = None
    assignee_id: int | None = Field(default=None, gt=0)
    status: GoalStatus = "not_started"


class GoalUpdate(_Text):
    title: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    target_date: date | None = None
    assignee_id: int | None = Field(default=None, gt=0)
    status: GoalStatus | None = None
    # Lets the client clear the optional fields explicitly (null alone means "unchanged").
    clear_target_date: bool = False
    clear_assignee: bool = False


class ActionItemCreate(_Text):
    description: str = Field(min_length=3, max_length=500)
    assigned_to_id: int = Field(gt=0)
    due_date: date | None = None
    goal_id: int | None = Field(default=None, gt=0)
    session_id: int | None = Field(default=None, gt=0)


class ActionItemUpdate(_Text):
    description: str | None = Field(default=None, min_length=3, max_length=500)
    assigned_to_id: int | None = Field(default=None, gt=0)
    due_date: date | None = None
    goal_id: int | None = Field(default=None, gt=0)
    session_id: int | None = Field(default=None, gt=0)
    status: ActionItemStatus | None = None
    clear_due_date: bool = False
    clear_goal: bool = False


class CloseMentorship(_Text):
    outcome_summary: str | None = Field(default=None, max_length=2000)


class FeedbackCreate(_Text):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)
