# AlumniConnect

A mentorship and networking platform for alumni. Members build a profile, get semantically ranked mentor suggestions, request mentorship, book sessions, chat, and use community and knowledge resources. Administrators moderate content and users.

## Features

- **Accounts:** registration, email verification, password login with emailed one-time code, password reset, optional Clerk sign-in
- **Profiles:** career domain, skills, goals, availability, picture upload, directory visibility
- **Mentor matching:** Sentence-Transformers embeddings stored in ChromaDB, ranked by cosine similarity
- **Mentorship:** requests, accept/decline, availability slots, bookings, per-mentorship chat, notifications
- **Networking and content:** connections, community feed, knowledge resources
- **Administration:** role-protected admin APIs and pages, audited one-time admin bootstrap

## Repository layout

| Path | Contents |
|---|---|
| `backend/` | FastAPI app (`app/api`, `app/models`, `app/schemas`, `app/services`, `app/ml`), tests in `backend/tests` |
| `frontend/` | React 19 + Vite client |
| `infrastructure/` | `docker-compose.yml` for a local PostgreSQL |
| `data/` | Data notes (see `data/README.md`) |
| `docs/` | Design notes and the Chapters 4-6 draft |
| `.github/workflows/ci.yml` | CI: backend tests, frontend lint and build |

## Prerequisites

- Python 3.13, Node.js 22, Git
- PostgreSQL 16 (via Docker below) or any SQLAlchemy-supported database URL
- A local Sentence-Transformers model folder for mentor matching (model files are git-ignored under `backend/ml_models/`)

## Setup

1. **Configuration.** Copy `.env.example` to `.env` in the repository root and fill it in. Never commit `.env`.
   - `DATABASE_URL`, e.g. `postgresql+psycopg://alumniconnect:alumniconnect_dev@localhost:5432/alumniconnect`
   - `SECRET_KEY`: generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`
   - `EMBEDDING_MODEL`: path to the model folder; `CHROMA_PERSIST_DIRECTORY`: vector store folder
   - SMTP settings for email (see `backend/EMAIL_AND_SOCIAL_LOGIN_SETUP.md`); Clerk keys are optional (see `docs/clerk-authentication.md`)
   - Frontend: optionally create `frontend/.env.local` with `VITE_API_BASE_URL` (default `http://127.0.0.1:8000`) and `VITE_CLERK_PUBLISHABLE_KEY`
2. **Database** (optional, local Postgres):
   ```powershell
   docker compose -f infrastructure/docker-compose.yml up -d
   ```
3. **Backend:**
   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
4. **Frontend:**
   ```powershell
   cd frontend
   npm ci
   ```

## Run

```powershell
# Backend (tables are created on startup) - from backend/
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

# Optional demo mentors - from backend/
.\.venv\Scripts\python.exe seed_mentors.py

# Frontend - from frontend/
npm run dev
```

API docs: http://127.0.0.1:8000/docs. App: http://localhost:5173.

To create the first administrator, follow `backend/ADMIN_SETUP.md`.

## Test

```powershell
# Backend - from backend/
.\.venv\Scripts\python.exe -m pytest -q

# Frontend - from frontend/
npm run lint
npm run build
```

Backend tests use an in-memory SQLite database and do not touch your configured database. The same checks run in GitHub Actions on every push and pull request; the backend job uploads a JUnit report as an artifact.

## Evidence and evaluation

```powershell
# from backend/ (needs the model folder from EMBEDDING_MODEL; set DATABASE_URL and SECRET_KEY)
.\.venv\Scripts\python.exe -m evaluation.eval_matching          # writes docs/evidence/matching_eval.md/.json
.\.venv\Scripts\python.exe -m pytest -q -W ignore --junitxml=pytest-report.xml
.\.venv\Scripts\python.exe -m evaluation.make_test_record pytest-report.xml ../docs/evidence/test_record.md
```

Results and discussion are in `docs/chapters-4-6-draft.md` (Chapter 5) and `docs/evidence/`.

## Known limitations

- No automated frontend or end-to-end tests yet; browser workflows are checked manually.
- Mentor matching has only a small synthetic baseline evaluation (21 queries, author-labelled); it does not show the fine-tuned model beating a keyword baseline.
- No performance, load or usability measurements yet.
- Email delivery depends on SMTP configuration; social sign-in needs registered provider apps.
- No production deployment yet (planned for Sprint III).
