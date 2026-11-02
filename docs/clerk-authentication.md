# Clerk authentication setup and migration notes

## Local configuration

Create `frontend/.env.local` with the Clerk development publishable key and the API URL:

```dotenv
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Set these backend variables in the local backend environment:

```dotenv
CLERK_SECRET_KEY=sk_test_...
CLERK_JWT_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
CLERK_AUTHORIZED_PARTIES=http://localhost:5173,http://127.0.0.1:5173
```

The API uses Clerk's `clerk-backend-api` session-token verifier with the secret key, optional public JWT key, an explicit session-token allow-list and configured authorized parties. Keep the secret key in the backend environment only. The frontend obtains a fresh short-lived session token through Clerk and sends it as a Bearer token. AlumniConnect continues to load roles and permissions from its own database.

## Clerk Dashboard

Create a Clerk application and enable Google, GitHub and Apple under social connections. Configure OAuth client credentials and provider redirect URLs in Clerk and in each provider console. Add the local frontend origin (`http://localhost:5173`) to Clerk's allowed origins. The app uses `/sso-callback` as the OAuth callback route and `/auth/complete` as the post-authentication destination. Repeat the configuration with production origins and live keys before deployment. Provider sign-in was not exercised because this workspace has no Clerk application keys or provider credentials.

## Identity and database migration

On startup, the backend performs an additive migration that creates a nullable, unique `users.clerk_user_id` column and index. Existing users, password hashes, profiles, mentorships and other relationships remain unchanged. During Clerk session setup, the backend links an unlinked AlumniConnect account when Clerk's Backend API confirms the same verified primary email address. It preserves the existing role and refuses to replace a different Clerk identity. Users whose existing account uses a different email can still link explicitly after proving control of both sessions: the local password session is sent in `Authorization`, and the Clerk session is sent in `X-Clerk-Authorization`.

New Clerk users complete AlumniConnect onboarding with a member role (`mentee` or `mentor`) and a required career profile. The backend verifies the Clerk session, retrieves the primary email from Clerk's Backend API, requires that email to be verified, rejects an email already used by an existing account, and creates the account/profile in one transaction. Administrator privileges are never selected in onboarding. Existing password-based registration and login remain available during migration.

Rollback is additive: stop the application, back up the database, and remove only the unique index and nullable identity column if no Clerk-linked account needs them. Do not remove user or profile records. Once users have linked identities, retain the mapping or first migrate identities through a reviewed procedure.

## Known boundaries

- Google, GitHub and Apple require Clerk Dashboard and provider-console configuration; code alone cannot activate the providers.
- The full existing backend suite imports Sentence Transformers at application startup. The focused token-verification tests are independent of that model dependency.
- The current frontend has no configured DOM/end-to-end test runner. The interactive provider flow and account linking need manual testing against a configured Clerk development instance.
- The social sign-in integration coexists with legacy email/password authentication. It does not silently migrate or delete legacy passwords.
