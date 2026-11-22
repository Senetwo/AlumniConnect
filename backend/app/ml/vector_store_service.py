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

        # Admin-curated library text (resources, announcements) for "Ask the library".
        # Holds only published, non-personal content; mentor and member data never go here.
        self.knowledge_collection = self.client.get_or_create_collection(
            name="knowledge_chunks",
            metadata={
                "description": "Embeddings of published library resources and announcements",
                "hnsw:space": "cosine"
            }
        )

    def upsert_knowledge(self, doc_id: str, embedding, document: str, metadata: dict):
        self.knowledge_collection.upsert(
            ids=[doc_id],
            embeddings=[embedding.tolist()],
            documents=[document],
            metadatas=[metadata]
        )

    def delete_knowledge(self, doc_id: str):
        self.knowledge_collection.delete(ids=[doc_id])

    def search_knowledge(self, embedding, n_results: int = 4):
        total = self.knowledge_collection.count()
        if total == 0:
            return []

        results = self.knowledge_collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=min(n_results, total)
        )

        return [
            {
                "id": doc_id,
                "document": document,
                "metadata": metadata,
                "similarity": float(1 - distance)
            }
            for doc_id, document, metadata, distance in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]

    def knowledge_ids(self):
        return self.knowledge_collection.get(include=[])["ids"]

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