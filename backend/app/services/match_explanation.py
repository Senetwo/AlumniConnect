"""Plain-language reasons shown next to a recommendation.

This only describes overlap that can be read straight from the two profiles. It does not
affect ranking: the order and score come from the Sentence-BERT similarity alone. A mentor
can rank highly with no listed reason, because the model also matches on meaning, not only
on shared words.
"""
import re

_STOPWORDS = {
    "that", "this", "with", "from", "have", "want", "wants", "become", "work", "working", "into", "about",
    "more", "also", "your", "their", "them", "than", "then", "like", "learn", "learning", "grow", "career",
    "path", "years", "year", "experience", "skills", "skill", "help", "need", "looking", "build", "improve",
    "develop", "development", "role", "roles", "field", "area", "areas", "will", "would", "could", "should",
}


def _split(value: str | None) -> list[str]:
    return [part.strip() for part in (value or "").split(",") if part.strip()]


def _pretty(value: str | None) -> str:
    """Profiles store some fields as slugs (flight-operations); show them as words."""
    text = (value or "").strip()
    if text and " " not in text and ("-" in text or "_" in text):
        return text.replace("-", " ").replace("_", " ").capitalize()
    return text


def _words(value: str | None) -> set[str]:
    return {word for word in re.findall(r"[a-z][a-z\-]{3,}", (value or "").lower()) if word not in _STOPWORDS}


def explain_match(mentee, mentor) -> list[str]:
    reasons: list[str] = []

    mentee_skills = {skill.lower() for skill in _split(mentee.skills)}
    shared = [skill for skill in _split(mentor.skills) if skill.lower() in mentee_skills]
    if shared:
        reasons.append(f"Shared skills: {', '.join(shared[:4])}")

    if (mentee.career_domain or "").strip().lower() == (mentor.career_domain or "").strip().lower():
        reasons.append(f"Same career domain: {_pretty(mentor.career_domain)}")
    if (mentee.career_path or "").strip().lower() == (mentor.career_path or "").strip().lower():
        reasons.append(f"Same career path: {_pretty(mentor.career_path)}")

    # Words the mentee wrote about their goals that also appear in what the mentor does.
    goal_words = _words(mentee.career_goals) | _words(mentee.mentorship_interests)
    mentor_words = _words(mentor.skills) | _words(mentor.career_path) | _words(mentor.bio) | _words(mentor.career_domain)
    overlap = sorted(goal_words & mentor_words)
    if overlap:
        reasons.append(f"Matches your goals: {', '.join(overlap[:3])}")

    return reasons
