from types import SimpleNamespace

from app.ml.matching_service import MatchingService


def make_profile(
    profile_id,
    career_domain,
    career_path,
    experience,
    skills,
    career_goals,
    availability
):
    return SimpleNamespace(
        id=profile_id,
        career_domain=career_domain,
        career_path=career_path,
        experience=experience,
        skills=skills,
        career_goals=career_goals,
        availability=availability
    )


def test_rank_matches_orders_by_similarity(monkeypatch):
    service = MatchingService()

    mentee = make_profile(
        8,
        "Technology & Digital",
        "Software Engineering",
        "2 years",
        "Python, FastAPI",
        "Become a software engineer",
        "Weekdays"
    )

    mentor_a = make_profile(
        1,
        "Technology & Digital",
        "Software Engineering",
        "8+ years",
        "Python, FastAPI",
        "Mentor software engineers",
        "Weekdays"
    )

    mentor_b = make_profile(
        2,
        "Finance",
        "Finance",
        "10+ years",
        "Accounting, Finance",
        "Develop finance professionals",
        "Weekends"
    )

    scores = {
        "Technology & Digital": 0.92,
        "Finance": 0.25,
    }

    monkeypatch.setattr(
        service,
        "similarity",
        lambda mentee, mentor: scores[mentor.career_domain]
    )

    matches = service.rank_matches(
        mentee,
        [mentor_b, mentor_a]
    )

    assert matches[0]["id"] == 1
    assert matches[1]["id"] == 2

    assert matches[0]["similarity_score"] == 92.0
    assert matches[1]["similarity_score"] == 25.0


def test_rank_matches_returns_all_mentors(monkeypatch):
    service = MatchingService()

    mentee = make_profile(
        8,
        "Technology & Digital",
        "Software Engineering",
        "2 years",
        "Python",
        "Become a software engineer",
        "Weekdays"
    )

    mentors = [
        make_profile(
            1,
            "Technology & Digital",
            "Software Engineering",
            "8+ years",
            "Python",
            "Mentor software engineers",
            "Weekdays"
        ),
        make_profile(
            2,
            "Engineering & Technical",
            "Aircraft Engineering",
            "10+ years",
            "Engineering",
            "Mentor engineers",
            "Weekends"
        ),
    ]

    monkeypatch.setattr(
        service,
        "similarity",
        lambda mentee, mentor: 0.8 if mentor.id == 1 else 0.2
    )

    matches = service.rank_matches(mentee, mentors)

    assert len(matches) == 2
    assert {match["id"] for match in matches} == {1, 2}


def test_rank_matches_handles_empty_mentor_list():
    service = MatchingService()

    mentee = make_profile(
        8,
        "Technology & Digital",
        "Software Engineering",
        "2 years",
        "Python",
        "Become a software engineer",
        "Weekdays"
    )

    matches = service.rank_matches(mentee, [])

    assert matches == []