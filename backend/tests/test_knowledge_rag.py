import re
import zlib
from types import SimpleNamespace

import anthropic
import httpx2
import numpy as np
import pytest

from app.api import knowledge as knowledge_api
from app.core.security import create_access_token
from app.database.database import settings
from app.ml import knowledge_index_service as index_module
from app.models.network import Announcement
from app.models.user import User
from app.services import rag_answer


DIM = 64


def auth_headers(user_id, role):
    token = create_access_token({"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


def make_user(db, email, role):
    user = User(
        full_name=email.split("@")[0],
        email=email,
        password_hash="not-used-in-this-test",
        role=role,
        is_email_verified=True,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


class FakeEmbedding:
    """Word-hash bag of words, so tests are fast and need no model."""

    def encode(self, text):
        vector = np.zeros(DIM)
        for word in re.findall(r"[a-z]+", text.lower()):
            vector[zlib.crc32(word.encode()) % DIM] += 1.0
        norm = np.linalg.norm(vector)
        return vector / norm if norm else vector


class FakeStore:
    def __init__(self):
        self.items = {}

    def upsert_knowledge(self, doc_id, embedding, document, metadata):
        self.items[doc_id] = (np.asarray(embedding), document, metadata)

    def delete_knowledge(self, doc_id):
        self.items.pop(doc_id, None)

    def knowledge_ids(self):
        return list(self.items)

    def search_knowledge(self, embedding, n_results=4):
        hits = [
            {"id": doc_id, "document": document, "metadata": metadata,
             "similarity": float(np.dot(embedding, vector))}
            for doc_id, (vector, document, metadata) in self.items.items()
        ]
        return sorted(hits, key=lambda hit: -hit["similarity"])[:n_results]


class FakeLLM:
    def __init__(self, text="CV tips are in passage [1].", stop_reason="end_turn", error=None):
        self.calls = []
        self.text = text
        self.stop_reason = stop_reason
        self.error = error
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(
            stop_reason=self.stop_reason,
            content=[SimpleNamespace(type="text", text=self.text)],
        )


@pytest.fixture
def store(monkeypatch):
    fake = FakeStore()
    embedding = FakeEmbedding()
    monkeypatch.setattr(rag_answer, "vector_store_service", fake)
    monkeypatch.setattr(rag_answer, "embedding_service", embedding)
    monkeypatch.setattr(index_module, "vector_store_service", fake)
    monkeypatch.setattr(index_module, "embedding_service", embedding)
    knowledge_api._ask_times.clear()
    return fake


@pytest.fixture
def llm(monkeypatch):
    fake = FakeLLM()
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(rag_answer, "get_client", lambda: fake)
    return fake


def add_passage(store, key, title, text, url="https://example.org/doc"):
    embedding = FakeEmbedding().encode(f"{title}. {text}")
    store.upsert_knowledge(key, embedding, f"{title}. {text}", {
        "source_type": "resource", "source_id": int(key.split(":")[1]), "title": title, "url": url,
    })


def ask(client, member, question="How do I write a strong CV?"):
    return client.post("/api/knowledge/ask", json={"question": question}, headers=auth_headers(member.id, member.role))


def test_ask_requires_login(client, store):
    assert client.post("/api/knowledge/ask", json={"question": "How do I write a CV?"}).status_code in (401, 403)


def test_grounded_answer_returns_only_cited_sources(client, db, store, llm):
    member = make_user(db, "member@test.example", "mentee")
    add_passage(store, "resource:1", "Writing a strong CV", "Keep your CV to two pages and lead with impact.")
    add_passage(store, "resource:2", "Interview preparation", "Practise common interview questions aloud.")

    response = ask(client, member, "How do I write a strong CV?")

    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is True and body["generated"] is True
    assert "[1]" in body["answer"]
    assert [source["title"] for source in body["sources"]] == ["Writing a strong CV"]
    prompt = llm.calls[0]["messages"][0]["content"]
    assert "Writing a strong CV" in prompt and "How do I write a strong CV?" in prompt
    assert llm.calls[0]["model"] == settings.llm_model


def test_no_relevant_passage_does_not_call_the_model(client, db, store, llm):
    member = make_user(db, "member2@test.example", "mentee")
    add_passage(store, "resource:1", "Writing a strong CV", "Keep your CV to two pages.")

    response = ask(client, member, "zebra quantum volcano")

    assert response.status_code == 200
    assert response.json() == {"answer": rag_answer.NOT_IN_LIBRARY, "sources": [], "grounded": False, "generated": False}
    assert llm.calls == []


def test_model_declining_or_refusing_is_reported_as_not_grounded(client, db, store, llm):
    member = make_user(db, "member3@test.example", "mentee")
    add_passage(store, "resource:1", "Writing a strong CV", "Keep your CV to two pages.")

    llm.text = "NOT_IN_LIBRARY"
    assert ask(client, member).json()["grounded"] is False

    llm.text, llm.stop_reason = "anything", "refusal"
    body = ask(client, member).json()
    assert body["grounded"] is False and body["sources"] == []


def test_without_api_key_returns_closest_resources_without_generated_text(client, db, store, monkeypatch):
    member = make_user(db, "member4@test.example", "mentee")
    add_passage(store, "resource:1", "Writing a strong CV", "Keep your CV to two pages.")
    add_passage(store, "resource:2", "Interview preparation", "Practise common interview questions aloud.")
    monkeypatch.setattr(settings, "llm_api_key", "")

    response = ask(client, member, "How do I write a strong CV?")

    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is True and body["generated"] is False
    assert "Writing a strong CV" in body["answer"] and "Keep your CV to two pages." in body["answer"]
    assert body["sources"][0]["title"] == "Writing a strong CV"


def test_without_api_key_unrelated_question_is_still_declined(client, db, store, monkeypatch):
    member = make_user(db, "member4b@test.example", "mentee")
    add_passage(store, "resource:1", "Writing a strong CV", "Keep your CV to two pages.")
    monkeypatch.setattr(settings, "llm_api_key", "")

    assert ask(client, member, "zebra quantum volcano").json()["grounded"] is False


def test_provider_failure_returns_502(client, db, store, monkeypatch):
    member = make_user(db, "member5@test.example", "mentee")
    add_passage(store, "resource:1", "Writing a strong CV", "Keep your CV to two pages.")
    failing = FakeLLM(error=anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.example.test")))
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(rag_answer, "get_client", lambda: failing)

    assert ask(client, member).status_code == 502


def test_question_length_is_validated(client, db, store, llm):
    member = make_user(db, "member6@test.example", "mentee")

    assert ask(client, member, "hi").status_code == 422
    assert ask(client, member, "x" * 501).status_code == 422
    assert llm.calls == []


def test_questions_are_rate_limited_per_member(client, db, store, llm, monkeypatch):
    member = make_user(db, "member7@test.example", "mentee")
    other = make_user(db, "member8@test.example", "mentee")
    add_passage(store, "resource:1", "Writing a strong CV", "Keep your CV to two pages.")
    monkeypatch.setattr(settings, "rag_questions_per_hour", 2)

    assert ask(client, member).status_code == 200
    assert ask(client, member).status_code == 200
    assert ask(client, member).status_code == 429
    assert ask(client, other).status_code == 200


def test_reindex_includes_only_published_content_and_is_admin_only(client, db, store):
    admin = make_user(db, "admin@test.example", "admin")
    member = make_user(db, "member9@test.example", "mentee")
    headers = auth_headers(admin.id, "admin")
    payload = {"category": "Careers", "resource_type": "Article", "url": "https://example.org/a"}

    published = client.post("/api/knowledge/", headers=headers, json={
        **payload, "title": "Published guide", "description": "A published guide to mentoring.", "is_published": True}).json()
    draft = client.post("/api/knowledge/", headers=headers, json={
        **payload, "title": "Draft guide", "description": "An unpublished draft guide.", "is_published": False}).json()
    note = Announcement(author_id=admin.id, title="Mentor week", body="Mentor week starts on Monday for everyone.")
    db.add(note)
    db.commit()
    store.upsert_knowledge("resource:999", np.ones(DIM), "stale", {"source_type": "resource", "source_id": 999})

    assert client.post("/api/knowledge/reindex", headers=auth_headers(member.id, "mentee")).status_code == 403
    result = client.post("/api/knowledge/reindex", headers=headers)

    assert result.status_code == 200
    assert set(store.knowledge_ids()) == {f"resource:{published['id']}", f"announcement:{note.id}"}
    assert f"resource:{draft['id']}" not in store.items
