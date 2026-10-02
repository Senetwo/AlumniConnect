from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.profile import Profile
from app.models.user import User
from app.ml.matching_service import matching_service

router = APIRouter(prefix="/api/matches", tags=["Matches"])


def build_matches(
    mentee: Profile,
    db: Session
):
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

    return matches


@router.get("/me")
def get_my_matches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "mentee":
        raise HTTPException(
            status_code=403,
            detail="Only mentees can retrieve mentor recommendations"
        )

    mentee = current_user.profile

    if not mentee:
        raise HTTPException(
            status_code=404,
            detail="Mentee profile not found"
        )

    matches = build_matches(
        mentee=mentee,
        db=db
    )

    return {
        "mentee_id": mentee.id,
        "matches": matches
    }


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

    matches = build_matches(
        mentee=mentee,
        db=db
    )

    return {
        "mentee_id": mentee.id,
        "matches": matches
    }