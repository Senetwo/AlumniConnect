from app.database.database import SessionLocal
from app.models.profile import Profile


mentors = [
    {
        "role": "mentor",
        "career_domain": "Technology & Digital",
        "career_path": "Software Engineering",
        "experience": "8+ years experience",
        "skills": "Python, FastAPI, Cloud Computing, Software Engineering, APIs",
        "career_goals": "Help emerging professionals build careers in software engineering, cloud technologies and digital systems.",
        "availability": "Weekday evenings",
    },
    {
        "role": "mentor",
        "career_domain": "Engineering & Technical",
        "career_path": "Aircraft Engineering",
        "experience": "10+ years experience",
        "skills": "Aircraft Systems, Engineering, Technical Operations, Safety, Leadership",
        "career_goals": "Support aspiring engineers interested in aviation engineering, technical operations and leadership.",
        "availability": "Weekday evenings",
    },
    {
        "role": "mentor",
        "career_domain": "Flight Operations",
        "career_path": "Flight Operations",
        "experience": "12+ years experience",
        "skills": "Flight Operations, Aviation Safety, Leadership, Crew Management",
        "career_goals": "Mentor professionals interested in flight operations, aviation safety and leadership.",
        "availability": "Weekend mornings",
    },
    {
        "role": "mentor",
        "career_domain": "Commercial & Corporate",
        "career_path": "Business Strategy",
        "experience": "7+ years experience",
        "skills": "Strategy, Finance, Business Analysis, Management, Leadership",
        "career_goals": "Help graduates develop careers in business strategy, management and corporate functions.",
        "availability": "Weekday evenings",
    },
    {
        "role": "mentor",
        "career_domain": "Cabin Crew & Customer Experience",
        "career_path": "Cabin Crew",
        "experience": "9+ years experience",
        "skills": "Customer Experience, Communication, Service, Safety, Leadership",
        "career_goals": "Support aspiring aviation professionals interested in cabin crew, customer experience and service leadership.",
        "availability": "Weekend afternoons",
    },
    {
        "role": "mentor",
        "career_domain": "Airport & Ground Operations",
        "career_path": "Ground Operations",
        "experience": "11+ years experience",
        "skills": "Airport Operations, Logistics, Customer Service, Safety, Operations Management",
        "career_goals": "Guide professionals interested in airport operations, logistics and aviation operations management.",
        "availability": "Weekday evenings",
    },
]


db = SessionLocal()

try:
    for mentor_data in mentors:
        mentor = Profile(**mentor_data)
        db.add(mentor)

    db.commit()

    print(f"Successfully added {len(mentors)} mentor profiles.")

finally:
    db.close()