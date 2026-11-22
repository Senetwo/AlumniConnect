import os
import uuid
from pathlib import Path

from fastapi import File, UploadFile
from fastapi.staticfiles import StaticFiles

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileResponse, ProfileUpdate
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.services.notification_service import create_notification
from app.ml.mentor_index_service import mentor_index_service


UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads" / "profiles"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB



router = APIRouter(
    prefix="/api/profiles",
    tags=["Profiles"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/me/photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(Profile)
        .filter(Profile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Create your profile before uploading a photo.",
        )

    allowed_types = {
        "image/jpeg": (".jpg", b"\xff\xd8\xff"),
        "image/png": (".png", b"\x89PNG\r\n\x1a\n"),
        "image/webp": (".webp", b"RIFF"),
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Upload a JPG, PNG, or WEBP image.",
        )

    contents = await file.read(MAX_IMAGE_SIZE + 1)

    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image must be 5 MB or smaller.",
        )

    extension, signature = allowed_types[file.content_type]

    if not contents.startswith(signature):
        raise HTTPException(
            status_code=400,
            detail="The file content does not match the selected image type.",
        )

    if file.content_type == "image/webp" and contents[8:12] != b"WEBP":
        raise HTTPException(
            status_code=400,
            detail="Invalid WEBP image.",
        )

    filename = f"{uuid.uuid4().hex}{extension}"
    destination = UPLOAD_DIR / filename

    try:
        destination.write_bytes(contents)

        profile.profile_picture_url = (
            f"{os.getenv('BASE_URL', 'http://127.0.0.1:8000')}/uploads/profiles/{filename}"
        )

        db.commit()
        db.refresh(profile)

        return {
            "profile_picture_url": profile.profile_picture_url,
            "message": "Profile photo uploaded successfully.",
        }

    except Exception:
        db.rollback()

        if destination.exists():
            destination.unlink()

        raise

    finally:
        await file.close()

@router.post("/", response_model=ProfileResponse)
def create_profile(
    profile: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create your own profile"
        )

    db_profile = Profile(
        user_id=profile.user_id,
        profile_picture_url=(
    str(profile.profile_picture_url)
    if profile.profile_picture_url
    else None
),
        career_domain=profile.career_domain,
        career_path=profile.career_path,
        experience=profile.experience,
        skills=", ".join(profile.skills),
        certifications=", ".join(profile.certifications),
        career_goals=profile.career_goals,
        mentorship_interests=", ".join(profile.mentorship_interests),
        availability=profile.availability,
        bio=profile.bio,
    )

    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    mentor_index_service.sync_profile(db_profile, current_user)

    return db_profile


@router.get("/", response_model=list[ProfileResponse])
def get_profiles(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    return db.query(Profile).all()


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(Profile)
        .filter(Profile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return profile


@router.patch("/me", response_model=ProfileResponse)
def update_my_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(Profile)
        .filter(Profile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    profile.career_domain = profile_data.career_domain
    profile.career_path = profile_data.career_path
    profile.experience = profile_data.experience
    profile.skills = ", ".join(profile_data.skills)
    profile.certifications = ", ".join(profile_data.certifications)
    profile.career_goals = profile_data.career_goals
    profile.mentorship_interests = ", ".join(
        profile_data.mentorship_interests
    )
    profile.availability = profile_data.availability
    profile.bio = profile_data.bio
    profile.profile_picture_url = (
        str(profile_data.profile_picture_url)
        if profile_data.profile_picture_url
        else None
    )
    was_directory_visible = profile.directory_visible
    profile.directory_visible = profile_data.directory_visible

    if profile.directory_visible and not was_directory_visible:
        members = db.query(User).filter(User.is_active.is_(True), or_(User.role.in_(["mentor", "mentee"]), User.community_role.in_(["mentor", "mentee"])), User.id != current_user.id).all()
        for member in members:
            create_notification(
                db,
                user_id=member.id,
                notification_type="new_directory_member",
                title="New profile in the Community Directory",
                message=f"{current_user.full_name} added a profile to the member directory.",
                resource_type="profile",
                resource_id=profile.id,
            )

    db.commit()
    db.refresh(profile)
    mentor_index_service.sync_profile(profile, current_user)

    return profile
