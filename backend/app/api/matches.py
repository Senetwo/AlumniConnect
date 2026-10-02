from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.profile import Profile
from app.models.user import User
from app.ml.matching_service import matching_service

router = APIRouter(prefix="/api/matches", tags=["Matches"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{mentee_id}")
def get_matches(
    mentee_id: int,
    db: Session = Depends(get_db)
):
    mentee = (
        db.query(Profile)
        .join(User)
        .filter(
            Profile.id == mentee_id,
            User.role == "mentee"
        )
        .first()
    )

    if not mentee:
        raise HTTPException(
            status_code=404,
            detail="Mentee profile not found"
        )

    candidate_results = (
        matching_service.retrieve_mentor_candidates(
            mentee,
            n_results=5
        )
    )

    matches = []

    for candidate in candidate_results:
        mentor = (
            db.query(Profile)
            .join(User)
            .filter(
                Profile.id == candidate["mentor_id"],
                User.role == "mentor"
            )
            .first()
        )

        if not mentor:
            continue

        matches.append({
            "id": mentor.id,
            "career_domain": mentor.career_domain,
            "career_path": mentor.career_path,
            "experience": mentor.experience,
            "skills": mentor.skills.split(","),
            "similarity_score": round(
                candidate["similarity"] * 100,
                2
            )
        })

    return {
        "mentee_id": mentee.id,
        "matches": matches
    }