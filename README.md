# AlumniConnect

A mentorship and networking platform for alumni. Members build a profile, get semantically ranked mentor suggestions, request mentorship, book sessions, work together in a shared mentorship workspace, chat, and use the Knowledge Hub. Administrators manage users, moderation, and published resources.

## Features

- **Accounts:** registration, email verification, password login with emailed one-time code, password reset, optional Clerk sign-in
- **Profiles:** career domain, skills, goals, availability, picture upload, directory visibility
- **Mentor matching:** Sentence-Transformers embeddings stored in ChromaDB, ranked by cosine similarity
- **Mentorship:** requests, accept/decline, availability slots, bookings, per-mentorship chat, and notifications
- **Mentorship workspace:** schedule sessions, keep shared or private notes, set goals and action items, track progress, and close a mentorship with an optional outcome summary. Completed workspaces remain available as read-only records.
- **Networking and content:** connections, community feed, and a curated Knowledge Hub
- **Ask the library:** semantic search over published Knowledge Hub resources, with answers grounded in retrieved passages and source links. When the library does not contain enough information, the assistant says so rather than guessing.
- **Feedback and reminders:** private post-mentorship feedback, plus notifications for upcoming sessions and overdue action items
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
- A local Sentence-Transformers model folder for mentor matching and Knowledge Hub retrieval (model files are git-ignored under `backend/ml_models/`)
- An LLM API key for generated Ask the library answers (`LLM_API_KEY`); without it, resource browsing remains available but generated answers are not

## Setup

1. **Configuration.** Copy `.env.example` to `.env` in the repository root and fill it in. Never commit `.env`.
   - `DATABASE_URL`, e.g. `postgresql+psycopg://alumniconnect:alumniconnect_dev@localhost:5432/alumniconnect`
   - `SECRET_KEY`: generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`
   - `EMBEDDING_MODEL`: path to the model folder; `CHROMA_PERSIST_DIRECTORY`: vector store folder
   - `LLM_API_KEY`: provider API key for Ask the library; `LLM_MODEL`, `RAG_TOP_K`, and `RAG_MIN_SIMILARITY` optionally configure answer generation and retrieval
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

# Optional Knowledge Hub resources and semantic search index - from backend/
.\.venv\Scripts\python.exe seed_knowledge.py

# Frontend - from frontend/
npm run dev
```

API docs: http://127.0.0.1:8000/docs. App: http://localhost:5173.

The backend creates new workspace tables and applies the additive workspace migration at startup. Restart the backend after pulling changes. Existing bookings are linked to workspace sessions during migration. Run `seed_knowledge.py` to add the curated starter resources and rebuild their semantic index; it is safe to run again.

The workspace is available from accepted mentorships under **My mentorships** or the mentor dashboard. Session bookings stay linked to their workspace sessions, and private notes are visible only to their author. See [`docs/mentorship-workspace.md`](docs/mentorship-workspace.md) for access rules, API routes, and migration details.

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
.\.venv\Scripts\python.exe -m evaluation.eval_rag               # retrieval-only; no LLM calls
.\.venv\Scripts\python.exe -m pytest -q -W ignore --junitxml=pytest-report.xml
.\.venv\Scripts\python.exe -m evaluation.make_test_record pytest-report.xml ../docs/evidence/test_record.md
```

Results and discussion are in `docs/chapters-4-6-draft.md` (Chapter 5) and `docs/evidence/`. Workspace behavior and data model notes are in `docs/mentorship-workspace.md`.

## Known limitations

- No automated frontend or end-to-end tests yet; browser workflows are checked manually.
- Mentor matching has only a small synthetic baseline evaluation (21 queries, author-labelled); it does not show the fine-tuned model beating a keyword baseline.
- No performance, load or usability measurements yet.
- Email delivery depends on SMTP configuration; social sign-in needs registered provider apps.
- Ask the library requires both an embedding model and an LLM API key for generated answers; its retrieval evaluation uses a small synthetic question set.
- No production deployment yet (planned for Sprint III).
