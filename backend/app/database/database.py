from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


BASE_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = BASE_DIR / "backend"


class Settings(BaseSettings):
    app_env: str = "development"

    backend_host: str = "127.0.0.1"
    backend_port: int = 8000

    database_url: str

    secret_key: str

    chroma_persist_directory: str = "./chroma_data"

    # The fine-tuned model is shipped with the repository through Git LFS.
    # Relative overrides can be rooted at either the repository or backend directory.
    embedding_model: str = "backend/ml_models/alumniconnect_sbert_finetuned"

    llm_api_key: str = ""
    # "Ask the library": answers are generated only from retrieved library passages.
    llm_model: str = "claude-opus-5-5"
    rag_top_k: int = 4
    # Cosine similarity below this means the passage is not about the question; with no
    # passage above it the system answers "not in the library" without calling the LLM.
    rag_min_similarity: float = 0.25
    rag_questions_per_hour: int = 30
    email_verification_required: bool = True
    login_otp_required: bool = True
    # Development only: when email delivery fails, print one-time links and codes in the
    # backend terminal instead of failing. Off by default so codes are only ever sent by email.
    email_dev_fallback: bool = False
    # Demo/test accounts are stored as name+tag@gmail.com so their codes land in one inbox.
    # When on, members sign in with the clean tag@gmail.com form and never see the plus address.
    plus_alias_login: bool = False
    # How long a password sign-in stays valid. Sign-in already needs an emailed code.
    access_token_expire_minutes: int = 480
    frontend_base_url: str = "http://localhost:5173"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_use_ssl: bool = False
    smtp_use_starttls: bool = True
    admin_bootstrap_email: str = Field(default="", validation_alias="ALUMNICONNECT_ADMIN_EMAIL")
    admin_bootstrap_token: str = Field(default="", validation_alias="ALUMNICONNECT_ADMIN_TOKEN")
    clerk_secret_key: str = ""
    clerk_jwt_key: str = ""
    clerk_authorized_parties: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore"
    )


settings = Settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
