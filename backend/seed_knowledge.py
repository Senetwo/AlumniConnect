"""Add library resources and rebuild the "Ask the library" index.

Run from the backend folder:

    .venv\\Scripts\\python.exe seed_knowledge.py

Safe to run again: a resource whose URL already exists is skipped. Every resource links to
the public site of an established provider; descriptions say what the provider offers and
are written to be useful when a member asks a question, so keep them short and factual.
"""
from app.database.database import SessionLocal
from app.ml.knowledge_index_service import knowledge_index_service
from app.models.knowledge_resource import KnowledgeResource


resources = [
    # Career Development
    {
        "title": "LinkedIn Learning: career and professional skills",
        "description": "Video courses on writing a CV and professional profile, interview skills, communication, time management and leadership. Useful for preparing job applications and building professional skills at your own pace.",
        "category": "Career Development",
        "resource_type": "Learning platform",
        "url": "https://www.linkedin.com/learning/",
        "source_name": "LinkedIn Learning",
    },
    {
        "title": "The Muse: career advice",
        "description": "Articles on writing a CV and cover letter, preparing for interviews, negotiating a job offer and salary, and handling workplace challenges. Practical guidance for early and mid-career professionals.",
        "category": "Career Development",
        "resource_type": "Career advice articles",
        "url": "https://www.themuse.com/advice",
        "source_name": "The Muse",
    },
    {
        "title": "Learning How to Learn",
        "description": "A course on study techniques based on research about memory and focus, including spaced practice, avoiding procrastination and making time to rest. Helpful when studying for certifications or preparing for interviews.",
        "category": "Career Development",
        "resource_type": "Course",
        "url": "https://www.coursera.org/learn/learning-how-to-learn",
        "source_name": "Coursera",
        "source_author": "Barbara Oakley and Terrence Sejnowski",
    },
    {
        "title": "Harvard Business Review: negotiation",
        "description": "Articles on preparing for and conducting negotiations, including researching the market, understanding the other side's interests and making a counter-offer. Relevant to salary and job offer discussions.",
        "category": "Career Development",
        "resource_type": "Industry articles",
        "url": "https://hbr.org/topic/subject/negotiation",
        "source_name": "Harvard Business Review",
    },
    {
        "title": "Mind Tools: stress, leadership and management skills",
        "description": "Short guides on managing stress and avoiding burnout, setting boundaries, delegating, giving feedback and leading a team. Practical tools for people moving into their first management role.",
        "category": "Career Development",
        "resource_type": "Skills guides",
        "url": "https://www.mindtools.com/",
        "source_name": "Mind Tools",
    },
    {
        "title": "Atlassian Team Playbook",
        "description": "Free plays and exercises for teams, including running retrospectives, setting goals and improving communication and feedback. Useful for new team leaders who want practical routines.",
        "category": "Career Development",
        "resource_type": "Team guides",
        "url": "https://www.atlassian.com/team-playbook",
        "source_name": "Atlassian",
    },
    # Technical Skills
    {
        "title": "The Python Tutorial",
        "description": "Official step-by-step tutorial covering Python syntax, data structures, functions, modules, classes and error handling. A good starting point for learning Python.",
        "category": "Technical Skills",
        "resource_type": "Tutorial",
        "url": "https://docs.python.org/3/tutorial/",
        "source_name": "Python Software Foundation",
    },
    {
        "title": "pandas: getting started",
        "description": "Introductory tutorials for the pandas library: loading data, selecting and filtering rows, cleaning data and plotting. Useful for analysing spreadsheet-like data in Python.",
        "category": "Technical Skills",
        "resource_type": "Tutorial",
        "url": "https://pandas.pydata.org/docs/getting_started/index.html",
        "source_name": "pandas documentation",
    },
    {
        "title": "Kaggle Learn: short data science courses",
        "description": "Free short courses on Python, pandas, data visualisation, machine learning and SQL, with hands-on exercises on real datasets. Good for practising small data projects.",
        "category": "Technical Skills",
        "resource_type": "Learning platform",
        "url": "https://www.kaggle.com/learn",
        "source_name": "Kaggle",
    },
    {
        "title": "freeCodeCamp: learn to code",
        "description": "Free interactive curriculum covering web development, JavaScript, Python and data analysis, with projects for building a portfolio. Helpful for coding practice when preparing for technical roles.",
        "category": "Technical Skills",
        "resource_type": "Learning platform",
        "url": "https://www.freecodecamp.org/learn/",
        "source_name": "freeCodeCamp",
    },
    # Cloud Computing
    {
        "title": "Google Cloud Skills Boost",
        "description": "Hands-on labs, courses and learning paths for Google Cloud, including preparation for Google Cloud certifications. A way to practise cloud skills in a guided environment.",
        "category": "Cloud Computing",
        "resource_type": "Learning platform",
        "url": "https://www.cloudskillsboost.google/",
        "source_name": "Google Cloud",
    },
    {
        "title": "AWS Certification: choose a certification path",
        "description": "Overview of AWS certifications from foundational to professional level, with exam guides and preparation resources. Helps decide which entry-level certification to start with.",
        "category": "Cloud Computing",
        "resource_type": "Certification guide",
        "url": "https://aws.amazon.com/certification/",
        "source_name": "Amazon Web Services",
    },
    {
        "title": "Microsoft Learn: browse certifications",
        "description": "Browse Microsoft certifications by role and level, including Azure fundamentals, with study guides and practice assessments. Useful for choosing a first cloud certification.",
        "category": "Cloud Computing",
        "resource_type": "Certification guide",
        "url": "https://learn.microsoft.com/en-us/credentials/browse/",
        "source_name": "Microsoft Learn",
    },
    {
        "title": "Cisco Networking Academy",
        "description": "Courses on networking, cybersecurity and Python, with labs and certification preparation. Builds the networking foundations that cloud and infrastructure roles rely on.",
        "category": "Cloud Computing",
        "resource_type": "Learning platform",
        "url": "https://www.netacad.com/",
        "source_name": "Cisco",
    },
    # Aviation
    {
        "title": "SKYbrary: aviation safety knowledge base",
        "description": "Aviation safety knowledge base covering safety management, human factors, just culture and incident reporting. Explains why staff are encouraged to report errors without blame so that organisations can learn.",
        "category": "Aviation",
        "resource_type": "Knowledge base",
        "url": "https://skybrary.aero/",
        "source_name": "SKYbrary",
    },
    {
        "title": "IATA training",
        "description": "Training courses and diplomas for aviation professionals, including safety, operations, cargo and airline business topics. Useful for planning professional development in the industry.",
        "category": "Aviation",
        "resource_type": "Course catalogue",
        "url": "https://www.iata.org/en/training/",
        "source_name": "International Air Transport Association",
    },
    # Professional practice
    {
        "title": "Office of the Data Protection Commissioner, Kenya",
        "description": "The Kenyan regulator's guidance on the Data Protection Act, including the rights of data subjects and the obligations of organisations that handle personal data. Relevant when working with member or customer information.",
        "category": "Professional Practice",
        "resource_type": "Regulator guidance",
        "url": "https://www.odpc.go.ke/",
        "source_name": "Office of the Data Protection Commissioner",
    },
]


def main():
    db = SessionLocal()
    try:
        existing = {url for (url,) in db.query(KnowledgeResource.url).all()}
        added = 0
        for item in resources:
            if item["url"] in existing:
                continue
            db.add(KnowledgeResource(is_published=True, **item))
            added += 1
        db.commit()
        print(f"Added {added} resources ({len(resources) - added} already present).")

        result = knowledge_index_service.reindex_all(db)
        print(f"Library index rebuilt: {result['indexed']} items.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
