from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileResponse
from app.core.dependencies import get_current_user, require_role
from app.models.user import User

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

    return db_profile


@router.get("/", response_model=list[ProfileResponse])
def get_profiles(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    return db.query(Profile).all()