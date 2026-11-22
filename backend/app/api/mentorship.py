
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_current_user, get_db, community_role
from app.models.mentorship import Mentorship
from app.models.profile import Profile
from app.models.user import User
from app.schemas.mentorship import (
    MentorshipDecisionRequest,
    MentorshipRequestCreate,
    MentorshipResponse,
)
from app.services.notification_service import create_notification

router = APIRouter(prefix="/api/mentorships", tags=["Mentorships"])


@router.post(
    "/",
    response_model=MentorshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_mentorship_request(
    request_data: MentorshipRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if community_role(current_user) != "mentee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only mentees can request mentorship.",
        )

    mentee_profile = (
        db.query(Profile)
        .filter(Profile.user_id == current_user.id)
        .first()
    )
    if not mentee_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your profile must exist before requesting mentorship.",
        )

    if request_data.mentor_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot request mentorship from yourself.",
        )

    mentor = (
        db.query(User)
        .join(Profile, Profile.user_id == User.id)
        .filter(
            User.id == request_data.mentor_id,
            User.is_active.is_(True),
            (User.role == "mentor") | (User.community_role == "mentor"),
        )
        .first()
    )
    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor or mentor profile not found.",
        )

    existing_request = (
        db.query(Mentorship)
        .filter(
            Mentorship.mentee_id == current_user.id,
            Mentorship.mentor_id == mentor.id,
            Mentorship.status.in_(["pending", "accepted"]),
        )
        .first()
    )
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active mentorship request already exists.",
        )

    mentorship = Mentorship(
        mentee_id=current_user.id,
        mentor_id=mentor.id,
        motivation=request_data.motivation.strip(),
        status="pending",
    )

    try:
        db.add(mentorship)
        db.flush()
        create_notification(
            db,
            user_id=mentor.id,
            notification_type="mentorship_request",
            title="New mentee request",
            message=f"{current_user.full_name} sent you a mentorship request.",
            resource_type="mentorship",
            resource_id=mentorship.id,
        )
        create_notification(
            db,
            user_id=current_user.id,
            notification_type="mentorship_pending",
            title="Mentorship request sent",
            message=f"Your request to {mentor.full_name} is pending their response.",
            resource_type="mentorship",
            resource_id=mentorship.id,
        )
        db.commit()
        db.refresh(mentorship)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active mentorship request already exists.",
        )

    return mentorship


@router.get(
    "/incoming",
    response_model=list[MentorshipResponse],
)
def get_incoming_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if community_role(current_user) != "mentor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only mentors can view incoming requests.",
        )

    return (
        db.query(Mentorship)
        .options(joinedload(Mentorship.mentee), joinedload(Mentorship.mentor))
        .filter(Mentorship.mentor_id == current_user.id)
        .order_by(Mentorship.created_at.desc())
        .all()
    )


@router.get(
    "/outgoing",
    response_model=list[MentorshipResponse],
)
def get_outgoing_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if community_role(current_user) != "mentee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only mentees can view outgoing requests.",
        )

    return (
        db.query(Mentorship)
        .options(joinedload(Mentorship.mentee), joinedload(Mentorship.mentor))
        .filter(Mentorship.mentee_id == current_user.id)
        .order_by(Mentorship.created_at.desc())
        .all()
    )


@router.patch(
    "/{mentorship_id}/respond",
    response_model=MentorshipResponse,
)
def respond_to_request(
    mentorship_id: int,
    decision: MentorshipDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if community_role(current_user) != "mentor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only mentors can respond to mentorship requests.",
        )

    mentorship = (
        db.query(Mentorship)
        .filter(
            Mentorship.id == mentorship_id,
            Mentorship.mentor_id == current_user.id,
        )
        .first()
    )

    if not mentorship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentorship request not found.",
        )

    if mentorship.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending requests can be accepted or declined.",
        )

    mentorship.status = decision.decision
    mentorship.responded_at = datetime.now(timezone.utc)

    approved = mentorship.status == "accepted"
    create_notification(
        db,
        user_id=mentorship.mentee_id,
        notification_type="mentorship_approved" if approved else "mentorship_rejected",
        title="Mentorship request approved" if approved else "Mentorship request rejected",
        message=(
            f"{current_user.full_name} approved your mentorship request. You can now book a session."
            if approved
            else f"{current_user.full_name} declined your mentorship request. You can explore other mentors."
        ),
        resource_type="mentorship",
        resource_id=mentorship.id,
    )
    db.commit()
    db.refresh(mentorship)

    return mentorship
