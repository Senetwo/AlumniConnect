from sentence_transformers import SentenceTransformer

from app.database.database import settings


class EmbeddingService:

    def __init__(self):
        self.model = SentenceTransformer(
            settings.embedding_model
        )

    def encode(self, text: str):
        return self.model.encode(
            text,
            normalize_embeddings=True
        )


embedding_service = EmbeddingService()