from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_role
from app.models.community import (
    CommunityEvent,
    CommunityEventRsvp,
    CommunityPost,
    CommunityPostLike,
    JobOpportunity,
)
from app.models.network import UserBlock
from app.models.profile import Profile
from app.models.user import User

router = APIRouter(tags=["Community feed"])

DAILY_POST_LIMIT = 10
EmploymentType = Literal["Full-time", "Part-time", "Contract", "Internship"]


def _http_url(value: str | None) -> str | None:
    """Accept only http(s) links so a stored link can never run script when opened."""
    if value is None or not value.strip():
        return None
    value = value.strip()
    if not value.lower().startswith(("http://", "https://")) or " " in value:
        raise ValueError("Links must start with http:// or https://")
    return value


class PostCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class EventCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=10, max_length=4000)
    location: str = Field(min_length=2, max_length=200)
    starts_at: datetime
    ends_at: datetime | None = None
    link: str | None = Field(default=None, max_length=500)

    _link = field_validator("link")(_http_url)

    @model_validator(mode="after")
    def check_times(self):
        if self.starts_at.tzinfo is None or self.starts_at.utcoffset() is None:
            raise ValueError("starts_at must include a timezone.")
        if self.ends_at is not None:
            if self.ends_at.tzinfo is None or self.ends_at.utcoffset() is None:
                raise ValueError("ends_at must include a timezone.")
            if self.ends_at <= self.starts_at:
                raise ValueError("ends_at must be later than starts_at.")
        return self


class JobCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    company: str = Field(default="Kenya Airways", min_length=2, max_length=160)
    location: str = Field(min_length=2, max_length=200)
    employment_type: EmploymentType
    description: str = Field(min_length=10, max_length=4000)
    apply_url: str | None = Field(default=None, max_length=500)
    contact_email: EmailStr | None = None
    closes_at: datetime | None = None

    _apply_url = field_validator("apply_url")(_http_url)

    @model_validator(mode="after")
    def check_how_to_apply(self):
        if not self.apply_url and not self.contact_email:
            raise ValueError("Provide an application link or a contact email.")
        if self.closes_at is not None and (self.closes_at.tzinfo is None or self.closes_at.utcoffset() is None):
            raise ValueError("closes_at must include a timezone.")
        return self


def _aware(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _blocked_ids(db: Session, user_id: int):
    return db.query(UserBlock.blocked_id).filter(UserBlock.blocker_id == user_id).union(
        db.query(UserBlock.blocker_id).filter(UserBlock.blocked_id == user_id)
    )


# ---------------------------------------------------------------- posts

def _post_payload(post: CommunityPost, author: User, profile: Profile | None, likes: int, liked: bool, viewer: User):
    return {
        "id": post.id,
        "body": post.body,
        "created_at": post.created_at,
        "author": {
            "id": author.id,
            "full_name": author.full_name,
            "role": author.community_role or author.role,
            "career_path": profile.career_path if profile else None,
            "profile_picture_url": profile.profile_picture_url if profile else None,
        },
        "like_count": likes,
        "liked_by_me": liked,
        "can_delete": author.id == viewer.id or viewer.role == "admin",
    }


@router.get("/api/community/posts")
def list_posts(
    before_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=15, ge=1, le=50),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(CommunityPost, User, Profile).join(User, User.id == CommunityPost.author_id).outerjoin(
        Profile, Profile.user_id == User.id
    ).filter(User.is_active.is_(True), ~User.id.in_(_blocked_ids(db, current.id)))
    if before_id:
        query = query.filter(CommunityPost.id < before_id)
    rows = query.order_by(CommunityPost.id.desc()).limit(limit + 1).all()
    page = rows[:limit]
    ids = [post.id for post, _, _ in page]
    counts = dict(
        db.query(CommunityPostLike.post_id, func.count(CommunityPostLike.id))
        .filter(CommunityPostLike.post_id.in_(ids)).group_by(CommunityPostLike.post_id).all()
    ) if ids else {}
    mine = {
        row[0] for row in db.query(CommunityPostLike.post_id).filter(
            CommunityPostLike.post_id.in_(ids), CommunityPostLike.user_id == current.id
        ).all()
    } if ids else set()
    return {
        "items": [
            _post_payload(post, author, profile, counts.get(post.id, 0), post.id in mine, current)
            for post, author, profile in page
        ],
        "has_more": len(rows) > limit,
    }


@router.post("/api/community/posts", status_code=201)
def create_post(data: PostCreate, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    body = data.body.strip()
    if not body:
        raise HTTPException(422, "A post cannot be empty")
    since = datetime.now(timezone.utc) - timedelta(days=1)
    if db.query(CommunityPost.id).filter(CommunityPost.author_id == current.id, CommunityPost.created_at >= since).count() >= DAILY_POST_LIMIT:
        raise HTTPException(429, "Daily post limit reached. Please try again tomorrow.")
    post = CommunityPost(author_id=current.id, body=body)
    db.add(post)
    db.commit()
    db.refresh(post)
    profile = db.query(Profile).filter(Profile.user_id == current.id).first()
    return _post_payload(post, current, profile, 0, False, current)


@router.delete("/api/community/posts/{post_id}", status_code=204)
def delete_post(post_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    if post.author_id != current.id and current.role != "admin":
        raise HTTPException(403, "You can only delete your own posts")
    db.query(CommunityPostLike).filter(CommunityPostLike.post_id == post.id).delete(synchronize_session=False)
    db.delete(post)
    db.commit()


def _visible_post(db: Session, post_id: int, viewer: User) -> CommunityPost:
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post or post.author_id in {row[0] for row in _blocked_ids(db, viewer.id).all()}:
        raise HTTPException(404, "Post not found")
    return post


@router.put("/api/community/posts/{post_id}/like")
def like_post(post_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = _visible_post(db, post_id, current)
    if not db.query(CommunityPostLike.id).filter(CommunityPostLike.post_id == post.id, CommunityPostLike.user_id == current.id).first():
        db.add(CommunityPostLike(post_id=post.id, user_id=current.id))
        db.commit()
    count = db.query(func.count(CommunityPostLike.id)).filter(CommunityPostLike.post_id == post.id).scalar()
    return {"like_count": count, "liked_by_me": True}


@router.delete("/api/community/posts/{post_id}/like")
def unlike_post(post_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = _visible_post(db, post_id, current)
    db.query(CommunityPostLike).filter(
        CommunityPostLike.post_id == post.id, CommunityPostLike.user_id == current.id
    ).delete(synchronize_session=False)
    db.commit()
    count = db.query(func.count(CommunityPostLike.id)).filter(CommunityPostLike.post_id == post.id).scalar()
    return {"like_count": count, "liked_by_me": False}


# --------------------------------------------------------------- events

def _event_payload(event: CommunityEvent, going: int, mine: bool):
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "location": event.location,
        "starts_at": event.starts_at,
        "ends_at": event.ends_at,
        "link": event.link,
        "is_cancelled": event.is_cancelled,
        "going_count": going,
        "going_by_me": mine,
    }


def _events_with_counts(db: Session, events: list[CommunityEvent], viewer: User):
    ids = [event.id for event in events]
    counts = dict(
        db.query(CommunityEventRsvp.event_id, func.count(CommunityEventRsvp.id))
        .filter(CommunityEventRsvp.event_id.in_(ids)).group_by(CommunityEventRsvp.event_id).all()
    ) if ids else {}
    mine = {
        row[0] for row in db.query(CommunityEventRsvp.event_id).filter(
            CommunityEventRsvp.event_id.in_(ids), CommunityEventRsvp.user_id == viewer.id
        ).all()
    } if ids else set()
    return [_event_payload(event, counts.get(event.id, 0), event.id in mine) for event in events]


@router.get("/api/community/events")
def list_upcoming_events(limit: int = Query(default=10, ge=1, le=50), current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    events = db.query(CommunityEvent).filter(
        CommunityEvent.is_cancelled.is_(False),
        or_(CommunityEvent.starts_at >= now, CommunityEvent.ends_at >= now),
    ).order_by(CommunityEvent.starts_at.asc()).limit(limit).all()
    return _events_with_counts(db, events, current)


def _open_event(db: Session, event_id: int) -> CommunityEvent:
    event = db.query(CommunityEvent).filter(CommunityEvent.id == event_id).first()
    if not event or event.is_cancelled:
        raise HTTPException(404, "Event not found")
    end = _aware(event.ends_at) or _aware(event.starts_at)
    if end < datetime.now(timezone.utc):
        raise HTTPException(409, "This event has already taken place")
    return event


def _rsvp_state(db: Session, event_id: int, user_id: int):
    count = db.query(func.count(CommunityEventRsvp.id)).filter(CommunityEventRsvp.event_id == event_id).scalar()
    mine = db.query(CommunityEventRsvp.id).filter(CommunityEventRsvp.event_id == event_id, CommunityEventRsvp.user_id == user_id).first() is not None
    return {"going_count": count, "going_by_me": mine}


@router.put("/api/community/events/{event_id}/rsvp")
def rsvp_event(event_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = _open_event(db, event_id)
    if not db.query(CommunityEventRsvp.id).filter(CommunityEventRsvp.event_id == event.id, CommunityEventRsvp.user_id == current.id).first():
        db.add(CommunityEventRsvp(event_id=event.id, user_id=current.id))
        db.commit()
    return _rsvp_state(db, event.id, current.id)


@router.delete("/api/community/events/{event_id}/rsvp")
def cancel_rsvp(event_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = _open_event(db, event_id)
    db.query(CommunityEventRsvp).filter(
        CommunityEventRsvp.event_id == event.id, CommunityEventRsvp.user_id == current.id
    ).delete(synchronize_session=False)
    db.commit()
    return _rsvp_state(db, event.id, current.id)


# ----------------------------------------------------------------- jobs

def _job_payload(job: JobOpportunity):
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "employment_type": job.employment_type,
        "description": job.description,
        "apply_url": job.apply_url,
        "contact_email": job.contact_email,
        "closes_at": job.closes_at,
        "is_active": job.is_active,
        "created_at": job.created_at,
    }


@router.get("/api/community/jobs")
def list_jobs(limit: int = Query(default=10, ge=1, le=50), current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    jobs = db.query(JobOpportunity).filter(
        JobOpportunity.is_active.is_(True), or_(JobOpportunity.closes_at.is_(None), JobOpportunity.closes_at > now)
    ).order_by(JobOpportunity.created_at.desc()).limit(limit).all()
    return [_job_payload(job) for job in jobs]


# ---------------------------------------------------------------- admin

@router.get("/api/admin/community/events")
def admin_list_events(current: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    events = db.query(CommunityEvent).order_by(CommunityEvent.starts_at.desc()).limit(200).all()
    return _events_with_counts(db, events, current)


@router.post("/api/admin/community/events", status_code=201)
def admin_create_event(data: EventCreate, current: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    if data.starts_at <= datetime.now(timezone.utc):
        raise HTTPException(422, "An event must start in the future")
    event = CommunityEvent(
        created_by=current.id, title=data.title.strip(), description=data.description.strip(),
        location=data.location.strip(), starts_at=data.starts_at, ends_at=data.ends_at, link=data.link,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return _event_payload(event, 0, False)


@router.patch("/api/admin/community/events/{event_id}/cancel")
def admin_cancel_event(event_id: int, current: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    event = db.query(CommunityEvent).filter(CommunityEvent.id == event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")
    event.is_cancelled = True
    db.commit()
    return _event_payload(event, *(_rsvp_state(db, event.id, current.id)["going_count"], False))


@router.get("/api/admin/community/jobs")
def admin_list_jobs(current: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    jobs = db.query(JobOpportunity).order_by(JobOpportunity.created_at.desc()).limit(200).all()
    return [_job_payload(job) for job in jobs]


@router.post("/api/admin/community/jobs", status_code=201)
def admin_create_job(data: JobCreate, current: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    job = JobOpportunity(
        created_by=current.id, title=data.title.strip(), company=data.company.strip(), location=data.location.strip(),
        employment_type=data.employment_type, description=data.description.strip(), apply_url=data.apply_url,
        contact_email=str(data.contact_email) if data.contact_email else None, closes_at=data.closes_at,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return _job_payload(job)


@router.patch("/api/admin/community/jobs/{job_id}/close")
def admin_close_job(job_id: int, current: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    job = db.query(JobOpportunity).filter(JobOpportunity.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    job.is_active = False
    db.commit()
    return _job_payload(job)
