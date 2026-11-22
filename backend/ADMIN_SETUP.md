# One-time administrator setup

AlumniConnect registration accepts only the `mentor` and `mentee` roles. Admin access is granted by a local backend CLI command; there is no public admin-creation API. Admin endpoints continue to check the account role on the server.

## Before you begin

1. Confirm the exact email address you control and intend to administer the platform with. The current app does not implement email verification, so verify ownership outside the app before adding this address to the trusted backend configuration.
2. Register that address through the normal form as a mentor or mentee if it does not already have an account. The bootstrap command elevates an existing account and never creates a second account.
3. Use a trusted machine and the same backend environment/database that the app uses. Do not commit the bootstrap values or share them in chat.

## Configure and run

In the repository root `.env` (or the trusted backend process environment), temporarily configure:

```dotenv
ALUMNICONNECT_ADMIN_EMAIL=the-exact-account-email
ALUMNICONNECT_ADMIN_TOKEN=one-time-random-secret-at-least-32-characters
```

Generate a secret locally with PowerShell:

```powershell
backend\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

From the `backend` directory, run:

```powershell
.\.venv\Scripts\python.exe -m app.admin_bootstrap --email the-exact-account-email
```

Enter the token at the hidden prompt. The command refuses to run unless the email matches the trusted environment allowlist, the token is valid and sufficiently long, and the existing account is present. It elevates that row in place and writes an audit record. The audit table permits only one successful bootstrap. Remove both temporary environment values immediately after success, then sign out and sign back in so the new role is loaded into the session.

Visit `/admin` after signing in. Admin APIs independently enforce the `admin` role; hiding or showing frontend navigation does not grant access. A non-admin request must continue to receive HTTP 403.

If the bootstrap token is lost before success, replace it in the trusted environment. If the one-time audit record already exists, use a separately reviewed database operations procedure for any later role changes; do not expose a public promotion endpoint.
