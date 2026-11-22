from pathlib import Path
from threading import Lock

from app.database.database import BACKEND_DIR, BASE_DIR, settings


DEFAULT_MODEL_PATH = BACKEND_DIR / "ml_models" / "alumniconnect_sbert_finetuned"


class EmbeddingService:
    """Lazily load the configured SentenceTransformer model on first use.

    Keeping construction cheap lets API modules and tests import the application
    without loading a 90 MB model. The public ``model`` property remains available
    for callers that used the previous eager ``embedding_service.model`` interface.
    """

    def __init__(self):
        self._model = None
        self._model_lock = Lock()

    @staticmethod
    def _resolve_model_path() -> Path:
        configured_path = (settings.embedding_model or "").strip()
        if not configured_path:
            return DEFAULT_MODEL_PATH.resolve()

        model_path = Path(configured_path).expanduser()
        if model_path.is_absolute():
            return model_path.resolve()

        # Preserve compatibility with paths configured from the repository root
        # (./backend/ml_models/...) and from the backend working directory
        # (./ml_models/...). Never resolve an empty setting to the repository root.
        candidates = ((BASE_DIR / model_path).resolve(), (BACKEND_DIR / model_path).resolve())
        for candidate in candidates:
            if candidate.is_dir():
                return candidate

        # Return a deterministic, useful missing path. SentenceTransformer will
        # never receive BASE_DIR itself for an empty or invalid configuration.
        return candidates[0]

    @property
    def model(self):
        if self._model is None:
            with self._model_lock:
                if self._model is None:
                    model_path = self._resolve_model_path()
                    if not model_path.is_dir():
                        raise FileNotFoundError(
                            "SentenceTransformer model directory was not found: "
                            f"{model_path}. Set EMBEDDING_MODEL to the fine-tuned "
                            "model directory."
                        )
                    required_files = ("modules.json", "config.json")
                    missing_files = [name for name in required_files if not (model_path / name).is_file()]
                    if missing_files:
                        missing = ", ".join(missing_files)
                        raise ValueError(
                            f"Invalid SentenceTransformer model directory {model_path}; "
                            f"missing required file(s): {missing}."
                        )

                    # Import ML dependencies only when inference is first requested.
                    from sentence_transformers import SentenceTransformer

                    self._model = SentenceTransformer(str(model_path))
        return self._model

    def encode(self, text: str):
        return self.model.encode(text, normalize_embeddings=True)


embedding_service = EmbeddingService()
