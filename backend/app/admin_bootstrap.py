"""One-time, local-only elevation of an explicitly allowlisted existing account."""

import argparse
import getpass
import hmac
import sys

from sqlalchemy.exc import IntegrityError
from sqlalchemy import inspect, text

from app.database.database import SessionLocal, engine, settings
from app.models.admin_bootstrap import AdminBootstrapAudit
from app.models.user import User


def provision_admin(email: str, token: str) -> str:
    allowlisted_email = settings.admin_bootstrap_email.strip().casefold()
    configured_token = settings.admin_bootstrap_token
    normalized_email = email.strip().casefold()

    if not allowlisted_email or not configured_token:
        raise ValueError("Set ALUMNICONNECT_ADMIN_EMAIL and ALUMNICONNECT_ADMIN_TOKEN in the trusted backend environment first.")
    if not hmac.compare_digest(normalized_email, allowlisted_email):
        raise ValueError("The requested email does not match the configured administrator identity.")
    if len(configured_token) < 32 or not hmac.compare_digest(token, configured_token):
        raise ValueError("The one-time administrator token is invalid or too short.")

    AdminBootstrapAudit.__table__.create(bind=engine, checkfirst=True)
    user_columns = {column["name"] for column in inspect(engine).get_columns("users")}
    with engine.begin() as connection:
        if "community_role" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN community_role VARCHAR(20)"))
        if "is_active" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"))
    audit_columns = {
        column["name"]
        for column in inspect(engine).get_columns(AdminBootstrapAudit.__tablename__)
    }
    if "actor" not in audit_columns:
        with engine.begin() as connection:
            connection.execute(text(
                "ALTER TABLE admin_bootstrap_audit "
                "ADD COLUMN actor VARCHAR(80) NOT NULL DEFAULT 'local-cli'"
            ))

    db = SessionLocal()
    try:
        if db.query(AdminBootstrapAudit.id).first():
            raise ValueError("Administrator bootstrap has already been used.")

        user = db.query(User).filter(User.email.ilike(normalized_email)).first()
        if user is None:
            raise ValueError("No account exists for that email. Register a normal account first, then retry.")
        if user.role == "admin":
            raise ValueError("That account is already an administrator; no changes were made.")

        previous_role = user.role
        user.community_role = user.community_role or previous_role
        user.role = "admin"
        db.add(AdminBootstrapAudit(
            target_user_id=user.id,
            target_email=user.email,
            action=f"{previous_role}_to_admin",
        ))
        db.commit()
        return f"Administrator access granted to the existing account {user.email}. Sign in again to refresh its role."
    except IntegrityError as error:
        db.rollback()
        raise ValueError("Bootstrap was already used or the account could not be elevated safely.") from error
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Secure one-time AlumniConnect administrator setup.")
    parser.add_argument("--email", required=True, help="Exact email configured as ALUMNICONNECT_ADMIN_EMAIL")
    args = parser.parse_args()
    token = getpass.getpass("One-time admin bootstrap token: ")
    try:
        print(provision_admin(args.email, token))
        return 0
    except ValueError as error:
        print(f"Admin setup refused: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
