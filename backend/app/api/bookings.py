
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, community_role
from app.models.booking import Booking, MentorAvailability
from app.models.mentorship import Mentorship
from app.models.user import User
from app.models.notifications import Notification
from app.schemas.booking import (
    AvailabilityCreate,
    AvailabilityResponse,
    BookingCreate,
    BookingResponse,
)
from app.services.notification_service import create_notification

router = APIRouter(prefix="/api", tags=["Bookings"])


@router.post(
    "/availability",
    response_model=AvailabilityResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_availability(
    data: AvailabilityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if community_role(current_user) != "mentor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only mentors can publish availability.",
        )

    now = datetime.now(timezone.utc)
    start_at = data.start_at.astimezone(timezone.utc)
    end_at = data.end_at.astimezone(timezone.utc)

    if start_at <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Availability must be in the future.",
        )

    overlapping = (
        db.query(MentorAvailability)
        .filter(
            MentorAvailability.mentor_id == current_user.id,
            MentorAvailability.status.in_(["available", "booked"]),
            MentorAvailability.start_at < end_at,
            MentorAvailability.end_at > start_at,
        )
        .first()
    )

    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This slot overlaps existing availability.",
        )

    slot = MentorAvailability(
        mentor_id=current_user.id,
        start_at=start_at,
        end_at=end_at,
        status="available",
    )

    db.add(slot)
    db.commit()
    db.refresh(slot)

    return slot


@router.get(
    "/availability/mentor/{mentor_id}",
    response_model=list[AvailabilityResponse],
)
def list_mentor_availability(
    mentor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mentor = (
        db.query(User)
        .filter(User.id == mentor_id, User.is_active.is_(True), (User.role == "mentor") | (User.community_role == "mentor"))
        .first()
    )
    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor not found.",
        )

    now = datetime.now(timezone.utc)

    return (
        db.query(MentorAvailability)
        .filter(
            MentorAvailability.mentor_id == mentor_id,
            MentorAvailability.status == "available",
            MentorAvailability.start_at > now,
        )
        .order_by(MentorAvailability.start_at.asc())
        .all()
    )


@router.get("/availability/me", response_model=list[AvailabilityResponse])
def list_my_availability(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if community_role(current_user) != "mentor":
        raise HTTPException(status_code=403, detail="Only mentors can view their full schedule.")
    return (
        db.query(MentorAvailability)
        .filter(
            MentorAvailability.mentor_id == current_user.id,
            MentorAvailability.status.in_(["available", "booked"]),
        )
        .order_by(MentorAvailability.start_at.asc())
        .all()
    )


@router.post(
    "/bookings",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_booking(
    data: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if community_role(current_user) != "mentee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only mentees can book mentorship sessions.",
        )

    mentorship = (
        db.query(Mentorship)
        .filter(
            Mentorship.id == data.mentorship_id,
            Mentorship.mentee_id == current_user.id,
            Mentorship.status == "accepted",
        )
        .first()
    )

    if not mentorship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accepted mentorship not found.",
        )

    slot = (
        db.query(MentorAvailability)
        .filter(
            MentorAvailability.id == data.availability_id,
            MentorAvailability.mentor_id == mentorship.mentor_id,
            MentorAvailability.status == "available",
        )
        .with_for_update()
        .first()
    )

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This availability slot is no longer available.",
        )

    if slot.start_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This availability slot has already started.",
        )

    booking = db.query(Booking).filter(Booking.availability_id == slot.id).first()
    if booking and booking.status == "confirmed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This slot has already been booked.")
    if booking:
        booking.mentorship_id = mentorship.id
        booking.mentee_id = current_user.id
        booking.status = "confirmed"
    else:
        booking = Booking(
            availability_id=slot.id,
            mentorship_id=mentorship.id,
            mentee_id=current_user.id,
            status="confirmed",
        )
    slot.status = "booked"
    try:
        if booking.id is None:
            db.add(booking)
        db.flush()
        db.add(Notification(
            user_id=slot.mentor_id,
            type="booking_created",
            title="New mentoring session booked",
            message="A mentee has booked one of your available sessions.",
            resource_type="booking",
            resource_id=booking.id,
        ))
        db.commit()
        db.refresh(booking)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This slot has already been booked.",
        )

    return booking


@router.get(
    "/bookings/me",
    response_model=list[BookingResponse],
)
def list_my_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if community_role(current_user) == "mentee":
        query = db.query(Booking).filter(
            Booking.mentee_id == current_user.id
        )
    elif community_role(current_user) == "mentor":
        query = (
            db.query(Booking)
            .join(
                MentorAvailability,
                Booking.availability_id == MentorAvailability.id,
            )
            .filter(MentorAvailability.mentor_id == current_user.id)
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your role cannot access bookings.",
        )

    bookings = query.order_by(Booking.created_at.desc()).all()
    enriched = []
    for booking in bookings:
        slot = db.query(MentorAvailability).filter(MentorAvailability.id == booking.availability_id).first()
        mentorship = db.query(Mentorship).filter(Mentorship.id == booking.mentorship_id).first()
        mentor = db.query(User).filter(User.id == (slot.mentor_id if slot else None)).first()
        mentee = db.query(User).filter(User.id == booking.mentee_id).first()
        enriched.append({
            "id": booking.id,
            "availability_id": booking.availability_id,
            "mentorship_id": booking.mentorship_id,
            "mentee_id": booking.mentee_id,
            "status": booking.status,
            "created_at": booking.created_at,
            "start_at": slot.start_at if slot else None,
            "end_at": slot.end_at if slot else None,
            "mentor_name": mentor.full_name if mentor else None,
            "mentee_name": mentee.full_name if mentee else None,
        })
    return enriched


@router.patch("/bookings/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
        .with_for_update()
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )

    slot = (
        db.query(MentorAvailability)
        .filter(MentorAvailability.id == booking.availability_id)
        .with_for_update()
        .first()
    )

    is_mentee = booking.mentee_id == current_user.id
    is_mentor = slot is not None and slot.mentor_id == current_user.id

    if not (is_mentee or is_mentor):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot cancel this booking.",
        )

    if booking.status != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only confirmed bookings can be cancelled.",
        )

    if slot is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The associated availability slot was not found.",
        )

    if slot.start_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A session that has already started cannot be cancelled.",
        )

    booking.status = "cancelled"
    slot.status = "available"
    
    recipient_id = (
    slot.mentor_id
    if booking.mentee_id == current_user.id
    else booking.mentee_id
)
    
    create_notification(
    db,
    user_id=recipient_id,
    notification_type="booking_cancelled",
    title="Mentoring session cancelled",
    message="A mentoring session has been cancelled.",
    resource_type="booking",
    resource_id=booking.id,
)

    db.commit()
    db.refresh(booking)

    return booking
