import json
import sys
import types

from app.database.database import BACKEND_DIR, BASE_DIR, settings
from app.ml.embedding_service import DEFAULT_MODEL_PATH, EmbeddingService


def test_empty_model_setting_uses_backend_model_directory(monkeypatch):
    monkeypatch.setattr(settings, "embedding_model", "")

    resolved = EmbeddingService._resolve_model_path()

    assert resolved == DEFAULT_MODEL_PATH.resolve()
    assert resolved != BASE_DIR


def test_relative_model_path_resolves_from_repository_or_backend(monkeypatch, tmp_path):
    model = tmp_path / "backend" / "ml_models" / "custom"
    model.mkdir(parents=True)
    monkeypatch.setattr("app.ml.embedding_service.BASE_DIR", tmp_path)
    monkeypatch.setattr("app.ml.embedding_service.BACKEND_DIR", tmp_path / "backend")
    monkeypatch.setattr(settings, "embedding_model", "./backend/ml_models/custom")

    assert EmbeddingService._resolve_model_path() == model.resolve()


def test_model_load_is_lazy_and_model_property_preserves_interface(monkeypatch, tmp_path):
    model_path = tmp_path / "model"
    model_path.mkdir()
    (model_path / "modules.json").write_text("[]", encoding="utf-8")
    (model_path / "config.json").write_text(json.dumps({"model_type": "bert"}), encoding="utf-8")
    loaded = []

    class FakeSentenceTransformer:
        def __init__(self, path):
            loaded.append(path)

        def encode(self, text, normalize_embeddings):
            return text, normalize_embeddings

    module = types.ModuleType("sentence_transformers")
    module.SentenceTransformer = FakeSentenceTransformer
    monkeypatch.setitem(sys.modules, "sentence_transformers", module)
    monkeypatch.setattr(settings, "embedding_model", str(model_path))

    service = EmbeddingService()
    assert service._model is None
    assert loaded == []

    assert service.encode("profile") == ("profile", True)
    assert loaded == [str(model_path)]
    assert service.model is service._model


def test_backend_directory_is_repository_root_child():
    assert BACKEND_DIR == BASE_DIR / "backend"
