"""Hand-written evaluation set for mentor matching.

Provenance and limits (state these in the report):
* Profiles are synthetic and were written for this evaluation; they are NOT drawn from the
  fine-tuning data in ml_models/ and contain no real people. Whether the fine-tuning data
  overlaps these phrasings has not been verified.
* Relevance labels are binary and assigned by the author: a mentor is relevant to a mentee
  when both work in the same career area. The labels have not been reviewed by a domain
  expert or checked against real mentorship outcomes.
* With 14 mentors and 21 mentees the sample is small; treat results as a baseline, not proof.
"""

# area -> list of mentors (domain, path, skills, goals)
MENTORS = {
    "software": [
        ("Technology & Digital", "Software Engineering", "Python, FastAPI, Cloud Computing, APIs", "Support early-career developers building backend systems."),
        ("Technology & Digital", "Software Engineering", "JavaScript, React, Testing, DevOps", "Guide junior engineers on web application development."),
    ],
    "data": [
        ("Technology & Digital", "Data Science & Analytics", "Python, SQL, Machine Learning, Statistics", "Mentor analysts moving into machine learning roles."),
        ("Technology & Digital", "Data Science & Analytics", "Power BI, SQL, Data Visualisation, Reporting", "Help professionals turn data into business insight."),
    ],
    "aircraft": [
        ("Engineering & Technical", "Aircraft Engineering", "Aircraft Systems, Maintenance, Technical Operations, Safety", "Mentor aspiring aircraft maintenance engineers."),
        ("Engineering & Technical", "Aircraft Engineering", "Avionics, Inspection, Airworthiness, Engineering", "Guide technicians towards licensed engineer status."),
    ],
    "flightops": [
        ("Flight Operations", "Flight Operations", "Flight Planning, Aviation Safety, Crew Management, Navigation", "Guide professionals interested in flight operations and aviation leadership."),
        ("Flight Operations", "Pilot Operations", "Crew Resource Management, Decision Making, Aviation Safety, Leadership", "Support aspiring pilots with career and safety guidance."),
    ],
    "business": [
        ("Commercial & Corporate", "Business Strategy", "Strategy, Finance, Business Analysis, Management", "Mentor professionals interested in corporate strategy."),
        ("Commercial & Corporate", "Procurement & Supply Chain", "Negotiation, Supply Chain, Risk Management, Contracts", "Help early-career staff grow in procurement and commercial roles."),
    ],
    "cabin": [
        ("Cabin Crew & Customer Experience", "Cabin Crew", "Customer Experience, Communication, Service, Safety", "Help aspiring cabin crew build service and communication skills."),
        ("Cabin Crew & Customer Experience", "Customer Experience", "Complaint Handling, Service Design, Communication, Leadership", "Develop customer experience leaders in aviation."),
    ],
    "ground": [
        ("Airport & Ground Operations", "Ground Operations", "Airport Operations, Logistics, Operations Management, Safety", "Support professionals pursuing airport and ground operations careers."),
        ("Airport & Ground Operations", "Ground Handling", "Baggage Handling, Turnaround Management, Logistics, Customer Service", "Guide new staff in aircraft turnaround and ground handling."),
    ],
}

# area -> list of mentees (domain, path, skills, goals); 3 per area
MENTEES = {
    "software": [
        ("Technology & Digital", "Software Engineering", "Python, Git, REST APIs", "Learn how to design reliable backend services."),
        ("Technology & Digital", "Software Engineering", "HTML, JavaScript, React", "Become a confident front-end and full-stack developer."),
        ("Technology & Digital", "Software Engineering", "Java, SQL, Docker", "Move from graduate developer to a cloud engineering role."),
    ],
    "data": [
        ("Technology & Digital", "Data Science & Analytics", "Python, Pandas, Statistics", "Break into machine learning and predictive modelling."),
        ("Technology & Digital", "Data Science & Analytics", "Excel, SQL, Power BI", "Build dashboards that support management decisions."),
        ("Technology & Digital", "Data Science & Analytics", "R, SQL, Data Cleaning", "Grow from junior analyst to data scientist."),
    ],
    "aircraft": [
        ("Engineering & Technical", "Aircraft Engineering", "Hydraulics, Maintenance, Safety", "Qualify as a licensed aircraft maintenance engineer."),
        ("Engineering & Technical", "Aircraft Engineering", "Avionics, Electronics, Inspection", "Specialise in avionics and airworthiness."),
        ("Engineering & Technical", "Aircraft Engineering", "Technical Operations, Engineering, Documentation", "Understand careers in aircraft technical operations."),
    ],
    "flightops": [
        ("Flight Operations", "Pilot Operations", "Navigation, Aviation Safety, Decision Making", "Prepare for a commercial pilot career."),
        ("Flight Operations", "Flight Operations", "Flight Planning, Dispatch, Communication", "Grow into a flight operations controller role."),
        ("Flight Operations", "Flight Operations", "Crew Scheduling, Safety, Leadership", "Lead a crew management team."),
    ],
    "business": [
        ("Commercial & Corporate", "Business Strategy", "Finance, Excel, Business Analysis", "Move into corporate strategy and planning."),
        ("Commercial & Corporate", "Procurement & Supply Chain", "Negotiation, Vendor Management, Supply Chain", "Build a career in procurement and sourcing."),
        ("Commercial & Corporate", "Business Strategy", "Management, Market Research, Presentation", "Develop leadership skills for commercial management."),
    ],
    "cabin": [
        ("Cabin Crew & Customer Experience", "Cabin Crew", "Service, First Aid, Communication", "Prepare for a cabin crew career and passenger safety duties."),
        ("Cabin Crew & Customer Experience", "Customer Experience", "Customer Service, Complaint Handling", "Improve passenger satisfaction and service quality."),
        ("Cabin Crew & Customer Experience", "Cabin Crew", "Teamwork, Languages, Hospitality", "Progress to a senior cabin crew position."),
    ],
    "ground": [
        ("Airport & Ground Operations", "Ground Operations", "Logistics, Safety, Operations Management", "Move into airport operations management."),
        ("Airport & Ground Operations", "Ground Handling", "Baggage Handling, Customer Service", "Learn about aircraft turnaround and ramp operations."),
        ("Airport & Ground Operations", "Ground Operations", "Planning, Logistics, Teamwork", "Become a shift supervisor on the airport apron."),
    ],
}
