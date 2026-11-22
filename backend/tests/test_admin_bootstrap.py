import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.admin_bootstrap as bootstrap
from app.models.admin_bootstrap import AdminBootstrapAudit
from app.models.user import User


@pytest.fixture
def bootstrap_db(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    User.__table__.create(engine)
    AdminBootstrapAudit.__table__.create(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(bootstrap, "engine", engine)
    monkeypatch.setattr(bootstrap, "SessionLocal", sessions)
    monkeypatch.setattr(bootstrap.settings, "admin_bootstrap_email", "admin@example.test")
    monkeypatch.setattr(bootstrap.settings, "admin_bootstrap_token", "x" * 48)
    db = sessions()
    db.add(User(full_name="Admin Candidate", email="admin@example.test", password_hash="hash", role="mentee"))
    db.commit()
    yield db
    db.close()
    engine.dispose()


def test_bootstrap_elevates_only_allowlisted_existing_account(bootstrap_db):
    assert bootstrap.provision_admin("admin@example.test", "x" * 48).startswith("Administrator access granted")
    user = bootstrap_db.query(User).one()
    assert user.role == "admin"
    assert bootstrap_db.query(AdminBootstrapAudit).one().action == "mentee_to_admin"


def test_bootstrap_refuses_unlisted_identity(bootstrap_db):
    with pytest.raises(ValueError, match="does not match"):
        bootstrap.provision_admin("someone-else@example.test", "x" * 48)
    assert bootstrap_db.query(User).one().role == "mentee"


def test_bootstrap_can_only_be_used_once(bootstrap_db):
    bootstrap.provision_admin("admin@example.test", "x" * 48)
    with pytest.raises(ValueError, match="already been used"):
        bootstrap.provision_admin("admin@example.test", "x" * 48)
