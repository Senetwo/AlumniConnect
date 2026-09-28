from app.database.database import SessionLocal
from app.models.user import User
from app.models.profile import Profile


mentors = [
    {
        "full_name": "Alex Mwangi",
        "email": "alex.mwangi@example.com",
        "career_domain": "Technology & Digital",
        "career_path": "Software Engineering",
        "experience": "8+ years",
        "skills": [
            "Python",
            "FastAPI",
            "Cloud Computing",
            "Software Engineering",
            "APIs",
        ],
        "certifications": [
            "AWS Certified Cloud Practitioner",
        ],
        "career_goals": "Support emerging technology professionals and share practical software engineering experience.",
        "mentorship_interests": [
            "Backend Development",
            "Cloud Computing",
            "Software Engineering",
        ],
        "availability": "Weekday evenings",
        "bio": "Experienced software engineering professional interested in mentoring early-career technology professionals.",
    },
    {
        "full_name": "Brian Otieno",
        "email": "brian.otieno@example.com",
        "career_domain": "Engineering & Technical",
        "career_path": "Aircraft Engineering",
        "experience": "10+ years",
        "skills": [
            "Aircraft Systems",
            "Engineering",
            "Technical Operations",
            "Safety",
            "Leadership",
        ],
        "certifications": [],
        "career_goals": "Mentor aspiring aviation engineering professionals.",
        "mentorship_interests": [
            "Aircraft Engineering",
            "Technical Operations",
            "Aviation Safety",
        ],
        "availability": "Weekends",
        "bio": "Aviation engineering professional with experience in technical operations and safety.",
    },
    {
        "full_name": "Carol Wanjiku",
        "email": "carol.wanjiku@example.com",
        "career_domain": "Flight Operations",
        "career_path": "Flight Operations",
        "experience": "12+ years",
        "skills": [
            "Flight Operations",
            "Aviation Safety",
            "Leadership",
            "Crew Management",
        ],
        "certifications": [],
        "career_goals": "Guide professionals interested in flight operations and aviation leadership.",
        "mentorship_interests": [
            "Flight Operations",
            "Aviation Safety",
            "Leadership",
        ],
        "availability": "Weekday afternoons",
        "bio": "Experienced flight operations professional focused on aviation safety and leadership.",
    },
    {
        "full_name": "Daniel Kariuki",
        "email": "daniel.kariuki@example.com",
        "career_domain": "Commercial & Corporate",
        "career_path": "Business Strategy",
        "experience": "7+ years",
        "skills": [
            "Strategy",
            "Finance",
            "Business Analysis",
            "Management",
            "Leadership",
        ],
        "certifications": [],
        "career_goals": "Mentor professionals interested in business strategy and corporate leadership.",
        "mentorship_interests": [
            "Business Strategy",
            "Business Analysis",
            "Leadership",
        ],
        "availability": "Weekday evenings",
        "bio": "Corporate strategy professional with experience in business analysis and management.",
    },
    {
        "full_name": "Emily Achieng",
        "email": "emily.achieng@example.com",
        "career_domain": "Cabin Crew & Customer Experience",
        "career_path": "Cabin Crew",
        "experience": "9+ years",
        "skills": [
            "Customer Experience",
            "Communication",
            "Service",
            "Safety",
            "Leadership",
        ],
        "certifications": [],
        "career_goals": "Help aspiring customer experience professionals develop communication and leadership skills.",
        "mentorship_interests": [
            "Customer Experience",
            "Communication",
            "Leadership",
        ],
        "availability": "Weekends",
        "bio": "Customer experience professional with experience in service, safety, communication, and leadership.",
    },
    {
        "full_name": "Frank Kamau",
        "email": "frank.kamau@example.com",
        "career_domain": "Airport & Ground Operations",
        "career_path": "Ground Operations",
        "experience": "11+ years",
        "skills": [
            "Airport Operations",
            "Logistics",
            "Customer Service",
            "Safety",
            "Operations Management",
        ],
        "certifications": [],
        "career_goals": "Support professionals pursuing careers in airport and ground operations.",
        "mentorship_interests": [
            "Airport Operations",
            "Logistics",
            "Operations Management",
        ],
        "availability": "Weekday mornings",
        "bio": "Airport operations professional experienced in logistics, customer service, safety, and operations management.",
    },
]


db = SessionLocal()

try:
    for mentor in mentors:
        existing_user = (
            db.query(User)
            .filter(User.email == mentor["email"])
            .first()
        )

        if existing_user:
            print(f"Skipping existing mentor: {mentor['full_name']}")
            continue

        user = User(
            full_name=mentor["full_name"],
            email=mentor["email"],
            password_hash="DEMO_PASSWORD_HASH",
            role="mentor",
        )

        db.add(user)
        db.flush()

        profile = Profile(
            user_id=user.id,
            career_domain=mentor["career_domain"],
            career_path=mentor["career_path"],
            experience=mentor["experience"],
            skills=", ".join(mentor["skills"]),
            certifications=", ".join(mentor["certifications"]),
            career_goals=mentor["career_goals"],
            mentorship_interests=", ".join(
                mentor["mentorship_interests"]
            ),
            availability=mentor["availability"],
            bio=mentor["bio"],
        )

        db.add(profile)

    db.commit()
    print("Synthetic mentor seed completed successfully.")

except Exception:
    db.rollback()
    raise

finally:
    db.close()