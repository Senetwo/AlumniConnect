# Email verification and social sign-in

## Email verification

New account registration creates an unverified account and sends a one-use link that expires after 24 hours. Sign-in is blocked until that link is used. Existing database rows receive `is_email_verified = TRUE` during backend startup, so seeded/test users are not forced through verification.

In local `APP_ENV=development`, if SMTP is unavailable, verification and password-reset links are logged to the backend terminal so local development can continue. These links are one-time and expire; this fallback is disabled outside development. Do not use a shared or public development server.

Configure these values in the repository root `.env` before allowing new registrations:

Replace every example value below with real values from your mail provider. In particular, `your-smtp-host` is only a placeholder and will not send mail.

```dotenv
EMAIL_VERIFICATION_REQUIRED=true
FRONTEND_BASE_URL=http://localhost:5173
SMTP_HOST=your-smtp-host
SMTP_PORT=587
SMTP_USERNAME=your-smtp-user
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=no-reply@your-domain
SMTP_USE_SSL=false
SMTP_USE_STARTTLS=true
```

For SSL SMTP on port 465, set `SMTP_USE_SSL=true` and `SMTP_USE_STARTTLS=false`. Restart the backend after changing `.env`. If mail delivery is unavailable during registration, the account remains unverified and can request a replacement link from the login page after email delivery is restored.

For a Gmail account, use the following non-secret settings and fill in your own Gmail address and Google App Password locally:

```dotenv
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-full-gmail-address@gmail.com
SMTP_PASSWORD=your-google-app-password
SMTP_FROM_EMAIL=your-full-gmail-address@gmail.com
SMTP_USE_SSL=false
SMTP_USE_STARTTLS=true
```

Gmail requires 2-Step Verification and an App Password for SMTP. Use the 16-character App Password generated in your Google Account; your usual Google sign-in password will not work. Keep the password in `.env` only and never paste it into chat or commit the file.

## Social sign-in

The Google, Apple, Microsoft, LinkedIn, and GitHub marks are presentation only at this point; the application has no OAuth callback routes or provider client configuration. They cannot authenticate users yet. Each provider requires an application registered with that provider, client credentials, and exact local and production redirect URLs. Apple also requires its signing key and team/key identifiers. Do not place provider secrets in frontend variables or commit them.

To finish this safely, first register the provider applications and configure their credentials/redirect URLs. Social identity should be linked only to an existing account with a provider-verified email, or use a separate account-linking and role/profile onboarding flow.

## Sign-in code (two-step login)

Password sign-in is a two-step flow. After a correct email and password, `POST /api/auth/login` returns `mfa_required: true` and a `challenge_token`, and a six-digit code is emailed to the user. The code is finished with `POST /api/auth/login/verify-otp` and can be re-sent with `POST /api/auth/login/resend-otp` (30 second cooldown).

- Codes expire after 10 minutes, are single use, and the challenge is discarded after 5 wrong attempts.
- Only keyed digests of the code and challenge token are stored (`login_challenges` table).
- It uses the same SMTP settings as email verification. In `APP_ENV=development`, if SMTP delivery fails the code is printed in the backend terminal instead.
- Set `LOGIN_OTP_REQUIRED=false` to turn the step off. It is always skipped when `APP_ENV=test`.
- Google, Apple and GitHub sign-in go through Clerk and do not use this step; enable multi-factor authentication for them in the Clerk Dashboard.

## Checking Gmail delivery

Run `.venv\Scripts\python.exe check_email.py` from the `backend` folder. It tests the SMTP login and explains Gmail errors in plain language; add an address (`check_email.py you@gmail.com`) to also send a test message. Gmail needs an App Password, not the account password.

Sign-in codes, verification links and reset links are only sent by email. Setting `EMAIL_DEV_FALLBACK=true` (development only) prints them in the backend terminal when delivery fails, which is useful when Gmail is not configured yet.
