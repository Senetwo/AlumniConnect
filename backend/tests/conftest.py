import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database.database import Base
from app.models.user import User
from app.models.profile import Profile
from app.core.dependencies import get_db as dependency_get_db
from app.api.auth import get_db as auth_get_db
from app.api.profiles import get_db as profile_get_db
from app.api.mentorship import get_db as mentorship_get_db
from app.main import app
from app.database.database import settings


TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db, monkeypatch):
    monkeypatch.setattr(settings, "app_env", "test")
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[dependency_get_db] = override_get_db
    app.dependency_overrides[auth_get_db] = override_get_db
    app.dependency_overrides[profile_get_db] = override_get_db
    app.dependency_overrides[mentorship_get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
