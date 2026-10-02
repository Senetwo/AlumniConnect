import numpy as np

from app.ml.vector_store_service import VectorStoreService


def make_embedding(index: int):
    embedding = np.zeros(384, dtype=np.float32)
    embedding[index] = 1.0
    return embedding


def test_add_and_get_mentor():
    service = VectorStoreService()

    mentor_id = 999001
    embedding = make_embedding(0)

    service.add_mentor(
        mentor_id=mentor_id,
        embedding=embedding,
        metadata={
            "career_domain": "Technology & Digital",
            "career_path": "Software Engineering",
            "experience": "5 years",
        }
    )

    result = service.get_mentor(mentor_id)

    assert result["ids"] == [str(mentor_id)]
    assert result["metadatas"][0]["career_domain"] == "Technology & Digital"

    service.delete_mentor(mentor_id)


def test_search_mentors_returns_similarity():
    service = VectorStoreService()

    service.add_mentor(
        mentor_id=999002,
        embedding=make_embedding(0),
        metadata={
            "career_domain": "Technology & Digital",
            "career_path": "Software Engineering",
            "experience": "5 years",
        }
    )

    service.add_mentor(
        mentor_id=999003,
        embedding=make_embedding(1),
        metadata={
            "career_domain": "Finance",
            "career_path": "Finance",
            "experience": "10 years",
        }
    )

    results = service.search_mentors(
        make_embedding(0),
        n_results=2
    )

    assert results[0]["mentor_id"] == 999002
    assert results[0]["similarity"] > results[1]["similarity"]
    assert 0.0 <= results[0]["similarity"] <= 1.0

    service.delete_mentor(999002)
    service.delete_mentor(999003)


def test_vector_store_count():
    service = VectorStoreService()

    initial_count = service.count()

    mentor_id = 999004

    service.add_mentor(
        mentor_id=mentor_id,
        embedding=make_embedding(2),
        metadata={
            "career_domain": "Engineering & Technical",
            "career_path": "Engineering",
            "experience": "8 years",
        }
    )

    assert service.count() == initial_count + 1

    service.delete_mentor(mentor_id)

    assert service.count() == initial_count