from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileResponse


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


@router.post(
    "/",
    response_model=ProfileResponse
)
def create_profile(
    profile: ProfileCreate,
    db: Session = Depends(get_db)
):

    db_profile = Profile(
        role=profile.role,
        career_domain=profile.career_domain,
        career_path=profile.career_path,
        experience=profile.experience,
        skills=", ".join(profile.skills),
        career_goals=profile.career_goals,
        availability=profile.availability,
    )

    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)

    return db_profile

@router.get("/")
def get_profiles(db: Session = Depends(get_db)):
    return db.query(Profile).all() 