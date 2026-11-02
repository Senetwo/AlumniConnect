from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, community_role
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
                User.is_active.is_(True),
                # Platform admins moderate the community; they are not recommended as mentors.
                User.role != "admin",
                (User.role == "mentor") | (User.community_role == "mentor")
            )
            .first()
        )

        if not mentor:
            continue

        matches.append({
            "id": mentor.id,
            "user_id": mentor.user_id,
            "full_name": mentor.user.full_name,
            "career_domain": mentor.career_domain,
            "career_path": mentor.career_path,
            "experience": mentor.experience,
            "skills": [
                skill.strip()
                for skill in (mentor.skills or "").split(",")
                if skill.strip()
            ],
            "bio": mentor.bio,
            "availability": mentor.availability,
            "profile_picture_url": mentor.profile_picture_url,
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
    if community_role(current_user) != "mentee":
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


@router.get("/mentor/{mentor_id}")
def get_mentor_profile(
    mentor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if community_role(current_user) != "mentee" and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to view this mentor profile"
        )

    if community_role(current_user) == "mentee":
        if not current_user.profile:
            raise HTTPException(
                status_code=404,
                detail="Mentee profile not found"
            )

        candidate_ids = {
            int(candidate["mentor_id"])
            for candidate in matching_service.retrieve_mentor_candidates(
                current_user.profile,
                n_results=5
            )
        }
        if mentor_id not in candidate_ids:
            raise HTTPException(
                status_code=404,
                detail="Mentor profile not found"
            )

    mentor = (
        db.query(Profile)
        .join(User)
        .filter(
            Profile.id == mentor_id,
            User.is_active.is_(True),
            (User.role == "mentor") | (User.community_role == "mentor")
        )
        .first()
    )

    if not mentor:
        raise HTTPException(
            status_code=404,
            detail="Mentor profile not found"
        )

    return {
        "id": mentor.id,
        "user_id": mentor.user_id,
        "full_name": mentor.user.full_name,
        "career_domain": mentor.career_domain,
        "career_path": mentor.career_path,
        "experience": mentor.experience,
        "skills": [
            skill.strip()
            for skill in (mentor.skills or "").split(",")
            if skill.strip()
        ],
        "certifications": [
            item.strip()
            for item in (mentor.certifications or "").split(",")
            if item.strip()
        ],
        "availability": mentor.availability,
        "bio": mentor.bio,
        "profile_picture_url": mentor.profile_picture_url,
    }


@router.get("/{mentee_id}")
def get_matches(
    mentee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if community_role(current_user) != "mentee":
        raise HTTPException(
            status_code=403,
            detail="Only mentees can retrieve mentor recommendations"
        )

    if not current_user.profile or current_user.profile.id != mentee_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own recommendations"
        )

    mentee = (
        db.query(Profile)
        .join(User)
        .filter(
            Profile.id == mentee_id,
            User.id == current_user.id,
            (User.role == "mentee") | (User.community_role == "mentee")
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
