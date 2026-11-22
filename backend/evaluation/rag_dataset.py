"""Synthetic library and questions for evaluating "Ask the library" retrieval.

The library imitates short admin-curated resources. Each question is a paraphrase of one
document's topic written to share few words with it, and carries the index of the document
that should answer it. OUT_OF_LIBRARY questions have no answer in the library. Labels were
drafted for this evaluation and must be reviewed by the author before the results are cited.
"""

DOCUMENTS = [
    ("Writing a CV that gets interviews", "Keep your CV to two pages, lead with achievements rather than duties, and tailor the keywords to each role."),
    ("Preparing for technical interviews", "Practise coding problems, explain your reasoning aloud, and rehearse with mock interviews before the real one."),
    ("Getting started with cloud certifications", "Begin with an entry-level AWS or Azure certification, follow a study plan and use hands-on labs."),
    ("How to find and approach a mentor", "Clarify your goals, send a short specific message, and say exactly what kind of help you are asking for."),
    ("Making the most of mentoring sessions", "Agree an agenda, take notes, and follow up on the action items you agreed at the end of each session."),
    ("Negotiating your first salary", "Research the market range, weigh the whole package and practise making a counter-offer calmly."),
    ("Building a professional network", "Attend industry events, hold informational chats and keep in touch with alumni and former colleagues."),
    ("Learning Python for data analysis", "Learn pandas and notebooks, then practise on small projects such as cleaning and charting a public dataset."),
    ("Aviation safety culture and reporting", "A just culture encourages staff to report incidents and errors without blame so the organisation can learn."),
    ("Managing stress and avoiding burnout", "Set boundaries around working hours, make time to rest, and ask colleagues or managers for support."),
    ("Writing a LinkedIn profile that attracts recruiters", "Use a clear headline, a short summary of your strengths and a skills list that matches the jobs you want."),
    ("Moving into leadership", "Learn to delegate, give regular constructive feedback and invest in developing the people in your team."),
]

# (question, index of the document that answers it)
QUESTIONS = [
    ("What should I put on my résumé to get shortlisted?", 0),
    ("How long should my resume be and what should it highlight?", 0),
    ("Any advice for coding rounds when applying for engineering jobs?", 1),
    ("How can I rehearse for a job interview in software?", 1),
    ("Which entry-level qualifications should I get to start working with AWS or Azure?", 2),
    ("I want a credential for cloud computing, where do I begin?", 2),
    ("How do I ask a senior person to guide my career?", 3),
    ("What should my first message to a possible mentor say?", 3),
    ("How can I get more out of the meetings with my mentor?", 4),
    ("What should we do after a mentoring meeting ends?", 4),
    ("How much should I ask for in my first job offer?", 5),
    ("How do I counter an offer from an employer?", 5),
    ("How do I meet people in my industry?", 6),
    ("How can I stay in touch with former colleagues?", 6),
    ("Which libraries do analysts use with Python for spreadsheet-like data?", 7),
    ("What is a good first project to practise data work in Python?", 7),
    ("What is a just culture and why should I report mistakes at work?", 8),
    ("How do I feel safe reporting an incident at work?", 8),
    ("I am exhausted from work, what can I do?", 9),
    ("How do I draw limits so work does not take over my life?", 9),
    ("What should the top line of my LinkedIn page say to attract recruiters?", 10),
    ("How can I stand out to hiring managers on social networking sites?", 10),
    ("How do I start managing a team for the first time?", 11),
    ("How do I give my staff useful feedback?", 11),
]

OUT_OF_LIBRARY = [
    "What is the capital of Australia?",
    "How do I bake sourdough bread?",
    "Who won the football world cup in 2014?",
    "What is the best way to train for a marathon?",
    "How do I repair a leaking tap?",
    "What is the boiling point of mercury?",
]
