import chromadb

from app.database.database import settings


class VectorStoreService:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory
        )

        self.collection = self.client.get_or_create_collection(
            name="mentor_profiles",
            metadata={
                "description": "Semantic embeddings for AlumniConnect mentor profiles",
                "hnsw:space": "cosine"
            }
        )

    def add_mentor(
        self,
        mentor_id: int,
        embedding,
        metadata: dict
    ):
        self.collection.upsert(
            ids=[str(mentor_id)],
            embeddings=[embedding.tolist()],
            metadatas=[metadata]
        )

    def get_mentor(self, mentor_id: int):
        return self.collection.get(
            ids=[str(mentor_id)]
        )

    def search_mentors(
        self,
        embedding,
        n_results: int = 5
    ):
        results = self.collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=n_results
        )

        ids = results["ids"][0]
        distances = results["distances"][0]

        return [
            {
                "mentor_id": int(mentor_id),
                "distance": float(distance),
                "similarity": float(1 - distance)
            }
            for mentor_id, distance in zip(ids, distances)
        ]

    def delete_mentor(self, mentor_id: int):
        self.collection.delete(
            ids=[str(mentor_id)]
        )

    def count(self):
        return self.collection.count()


vector_store_service = VectorStoreService()