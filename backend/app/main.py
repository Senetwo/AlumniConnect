from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.database.database import engine, Base, SessionLocal, settings
from app.models.user import User
from app.models.profile import Profile
from app.models.mentorship import Mentorship
from app.api.auth import router as auth_router
from app.api.profiles import router as profile_router
from app.api.mentorship import router as mentorship_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.matches import router as matches_router
from sqlalchemy import inspect, text
from app.models.booking import MentorAvailability, Booking
from app.api.bookings import router as bookings_router
from app.api.chat import router as chat_router
from app.models.notifications import Notification
from app.api.notifications import router as notifications_router
import app.models.profile
import app.models.notifications
from app.models.knowledge_resource import KnowledgeResource
from app.models.network import ConnectionRequest, UserBlock, UserReport, NetworkMessage, Announcement
from app.models.admin_bootstrap import AdminBootstrapAudit
from app.models.login_challenge import LoginChallenge
from app.models.community import CommunityPost, CommunityPostLike, CommunityEvent, CommunityEventRsvp, JobOpportunity
from app.models.email_verification import EmailVerificationToken
from app.models.password_reset import PasswordResetToken
from app.models.admin_action import AdminActionAudit
from app.api.admin import router as admin_router
from app.api.knowledge import router as knowledge_router
from app.api.network import router as network_router
from app.api.community import router as community_router
from pathlib import Path
from fastapi.staticfiles import StaticFiles
def init_database():
    Base.metadata.create_all(bind=engine)


    inspector = inspect(engine)

    # An earlier schema forced requester_id < recipient_id on connection requests. The
    # current model identifies a pair by (pair_low_id, pair_high_id) and lets either
    # member send the request, so the old rule made some requests fail.
    if engine.dialect.name == "postgresql" and inspector.has_table("connection_requests"):
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE connection_requests DROP CONSTRAINT IF EXISTS ck_connection_pair_order"))

    # Legacy accounts predate verification and remain usable. New registrations
    # explicitly store is_email_verified=False in the ORM.
    if inspector.has_table("users"):
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        with engine.begin() as connection:
            if "clerk_user_id" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN clerk_user_id VARCHAR(255)"))
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_clerk_user_id ON users (clerk_user_id)"))
            if "community_role" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN community_role VARCHAR(20)"))
            if "is_active" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"))
            connection.execute(text("UPDATE users SET community_role = role WHERE community_role IS NULL AND role IN ('mentor', 'mentee')"))
            # Existing accounts promoted through the audited one-time flow retain their former member role.
            if inspect(engine).has_table("admin_bootstrap_audit"):
                connection.execute(text("""UPDATE users SET community_role = CASE
                    WHEN (SELECT action FROM admin_bootstrap_audit WHERE target_user_id = users.id) = 'mentor_to_admin' THEN 'mentor'
                    WHEN (SELECT action FROM admin_bootstrap_audit WHERE target_user_id = users.id) = 'mentee_to_admin' THEN 'mentee'
                    ELSE community_role END WHERE role = 'admin' AND community_role IS NULL"""))
        if "is_email_verified" not in user_columns:
            with engine.begin() as connection:
                connection.execute(text(
                    "ALTER TABLE users ADD COLUMN is_email_verified BOOLEAN NOT NULL DEFAULT TRUE"
                ))

    if inspector.has_table("profiles"):
        profile_columns = {
            column["name"]
            for column in inspector.get_columns("profiles")
        }

        if "profile_picture_url" not in profile_columns:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE profiles "
                        "ADD COLUMN profile_picture_url VARCHAR(1000)"
                    )
                )
        if "directory_visible" not in profile_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE profiles ADD COLUMN directory_visible BOOLEAN NOT NULL DEFAULT FALSE"))

    if inspector.has_table("knowledge_resources"):
        knowledge_columns = {column["name"] for column in inspector.get_columns("knowledge_resources")}
        with engine.begin() as connection:
            for column, declaration in (("source_name", "VARCHAR(200)"), ("source_author", "VARCHAR(200)"), ("publication_date", "DATE")):
                if column not in knowledge_columns:
                    connection.execute(text(f"ALTER TABLE knowledge_resources ADD COLUMN {column} {declaration}"))

    if inspector.has_table("connection_requests"):
        connection_columns = {column["name"] for column in inspector.get_columns("connection_requests")}
        with engine.begin() as connection:
            if "pair_low_id" not in connection_columns:
                connection.execute(text("ALTER TABLE connection_requests ADD COLUMN pair_low_id INTEGER"))
            if "pair_high_id" not in connection_columns:
                connection.execute(text("ALTER TABLE connection_requests ADD COLUMN pair_high_id INTEGER"))
            connection.execute(text(
                "UPDATE connection_requests SET "
                "pair_low_id = CASE WHEN requester_id < recipient_id THEN requester_id ELSE recipient_id END, "
                "pair_high_id = CASE WHEN requester_id > recipient_id THEN requester_id ELSE recipient_id END "
                "WHERE pair_low_id IS NULL OR pair_high_id IS NULL"
            ))
            connection.execute(text("ALTER TABLE connection_requests ALTER COLUMN pair_low_id SET NOT NULL"))
            connection.execute(text("ALTER TABLE connection_requests ALTER COLUMN pair_high_id SET NOT NULL"))

        unique_constraints = {
            constraint["name"]
            for constraint in inspect(engine).get_unique_constraints("connection_requests")
        }
        if "uq_connection_pair" not in unique_constraints:
            with engine.begin() as connection:
                connection.execute(text(
                    "ALTER TABLE connection_requests ADD CONSTRAINT uq_connection_pair "
                    "UNIQUE (pair_low_id, pair_high_id)"
                ))

    if inspector.has_table("mentorships"):
        columns = {
            column["name"]
            for column in inspector.get_columns("mentorships")
        }

        if "motivation" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE mentorships "
                        "ADD COLUMN motivation TEXT"
                    )
                )

                connection.execute(
                    text(
                        "UPDATE mentorships "
                        "SET motivation = 'Legacy request' "
                        "WHERE motivation IS NULL"
                    )
                )
                connection.execute(
                    text(
                        "ALTER TABLE mentorships "
                        "ALTER COLUMN motivation SET NOT NULL"
                    )
                )

    # Keep the hub useful on a fresh installation and when existing admin drafts
    # are unpublished. Add each starter only when its URL is not already present.
    with SessionLocal() as db:
        starter_resources = [
            KnowledgeResource(
                    title="Kenya Airways Blog: airline and aviation perspectives",
                    description="Read official Kenya Airways articles and updates about airline operations, travel, and the wider aviation industry. The original articles remain on the Kenya Airways site.",
                    category="Aviation",
                    resource_type="Industry articles",
                    url="https://corporate.kenya-airways.com/en/press-room/kq-blog/",
                    source_name="Kenya Airways",
                    is_published=True,
            ),
            KnowledgeResource(
                    title="Microsoft Learn: guided technical learning",
                    description="Explore self-paced modules and learning paths covering cloud, data, AI, security, and Microsoft tools. Certification exams and some related services may have separate costs.",
                    category="Technical Skills",
                    resource_type="Learning platform",
                    url="https://learn.microsoft.com/en-us/training/",
                    source_name="Microsoft Learn",
                    is_published=True,
            ),
            KnowledgeResource(
                    title="AWS Skill Builder: cloud learning paths",
                    description="Use AWS training courses and learning plans to build cloud skills at your own pace. Availability of courses, hands-on labs, and subscriptions can vary.",
                    category="Technical Skills",
                    resource_type="Learning platform",
                    url="https://skillbuilder.aws/",
                    source_name="AWS Skill Builder",
                    is_published=True,
            ),
            KnowledgeResource(
                    title="ICAO training catalogue: aviation sustainability",
                    description="Browse official ICAO training opportunities related to aviation sustainability and safety. Check the course page for current dates, prerequisites, and fees before enrolling.",
                    category="Aviation",
                    resource_type="Course catalogue",
                    url="https://igat.icao.int/ated/trainingcatalogue/Course/6350",
                    source_name="International Civil Aviation Organization",
                    is_published=True,
            ),
        ]
        existing_urls = {url for (url,) in db.query(KnowledgeResource.url).all()}
        missing_resources = [resource for resource in starter_resources if resource.url not in existing_urls]
        if missing_resources:
            db.add_all(missing_resources)
            db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.app_env != "test":
        init_database()
    yield


app = FastAPI(
    title="AlumniConnect API",
    version="1.0.0",
    lifespan=lifespan,
)

UPLOADS_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOADS_DIR)),
    name="uploads",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "AlumniConnect API is running",
        "database_configured": True
    }


app.include_router(profile_router)
app.include_router(matches_router)
app.include_router(auth_router)
app.include_router(mentorship_router)
app.include_router(bookings_router)
app.include_router(chat_router)
app.include_router(notifications_router)
app.include_router(knowledge_router)
app.include_router(network_router)
app.include_router(community_router)
app.include_router(admin_router)
