from types import SimpleNamespace

import pytest

from app.database.database import settings
from app.ml.mentor_index_service import mentor_index_service


@pytest.fixture
def calls(monkeypatch):
    recorded = []
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(mentor_index_service, "index_mentor", lambda profile: recorded.append(("index", profile.id)))
    monkeypatch.setattr(mentor_index_service, "remove_mentor", lambda profile_id: recorded.append(("remove", profile_id)))
    return recorded


def user(role, community_role=None, active=True):
    return SimpleNamespace(role=role, community_role=community_role, is_active=active)


def test_mentor_profiles_are_indexed(calls):
    mentor_index_service.sync_profile(SimpleNamespace(id=7), user("mentor", "mentor"))

    assert calls == [("index", 7)]


def test_mentees_and_suspended_mentors_are_removed_from_the_index(calls):
    mentor_index_service.sync_profile(SimpleNamespace(id=8), user("mentee", "mentee"))
    mentor_index_service.sync_profile(SimpleNamespace(id=9), user("mentor", "mentor", active=False))

    assert calls == [("remove", 8), ("remove", 9)]


def test_index_failures_never_break_the_request(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "development")

    def broken(profile):
        raise RuntimeError("vector store unavailable")

    monkeypatch.setattr(mentor_index_service, "index_mentor", broken)

    mentor_index_service.sync_profile(SimpleNamespace(id=1), user("mentor", "mentor"))


def test_nothing_is_indexed_when_running_tests(monkeypatch):
    called = []
    monkeypatch.setattr(settings, "app_env", "test")
    monkeypatch.setattr(mentor_index_service, "index_mentor", lambda profile: called.append(profile.id))

    mentor_index_service.sync_profile(SimpleNamespace(id=1), user("mentor", "mentor"))

    assert called == []
