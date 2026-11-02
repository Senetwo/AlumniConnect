
from pathlib import Path

from sentence_transformers import SentenceTransformer

from app.database.database import settings, BASE_DIR


class EmbeddingService:

    def __init__(self):
        model_path = Path(settings.embedding_model)

        if not model_path.is_absolute():
            model_path = (BASE_DIR / model_path).resolve()

        self.model = SentenceTransformer(str(model_path))

    def encode(self, text: str):
        return self.model.encode(
            text,
            normalize_embeddings=True
        )


embedding_service = EmbeddingService()
