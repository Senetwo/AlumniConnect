# Mentorship workspace

Lifecycle tools for an accepted mentorship: sessions, meeting notes, goals, action items, progress, timeline and closure. Matching (Sentence-BERT, Chroma, `/api/matches`) is untouched.

## Access rules
- Every route under `/api/mentorships/{id}/...` loads the mentorship by id, requires the caller to be its mentor or mentee, and requires status `accepted` or `completed`. Anyone else gets **404**, so ids cannot be probed. Administrators get no extra access.
- Writes need `accepted`. A `completed` mentorship is read-only (409).
- Accepting a community connection never creates a mentorship or a workspace; the two features share no table.
- Private notes are filtered in one query (`visible_notes_query`: shared, or `author_id` = caller). Every endpoint that returns notes uses it. Private notes write no activity event, and another participant's private note answers 404 on edit.

## Data model (new tables; all rows reference `mentorships.id`)
| Table | Purpose |
|---|---|
| `mentorship_sessions` | Title, schedule, duration, virtual / in person, link or location, agenda, status (`scheduled` / `completed` / `cancelled`). Nullable unique `booking_id` links it to an existing booking. |
| `session_notes` | Six structured sections, `visibility` (`shared` / `private`, required), author, timestamps. |
| `mentorship_goals` | Title, description, target date, status, responsible person (NULL = both). |
| `action_items` | Description, assignee, due date, status, optional goal and session. |
| `mentorship_activity_events` | Timeline and goal history. Short summaries only, never note text. |

Changes to `mentorships`: nullable `closed_at`, `closed_by_id`, `outcome_summary`; status check widened to include `completed`. The start date is the existing `responded_at`.

"Mentorship established" and "Mentorship completed" are read from `responded_at` / `closed_at`, not stored twice.

## Bookings
A confirmed booking creates (or reactivates) a linked session, and cancelling either one cancels the other and frees the slot. The time of a booked session cannot be edited; cancel and book another slot. Existing bookings get sessions through the migration.

## Progress method
- Goals: completed goals / goals that are not on hold.
- Action items: completed / all.
- Shown separately, never blended, and `null` (no percentage shown) when there is nothing to count. Sessions are counts only.
- "Needs attention" lists overdue action items, goals past their target date and past sessions still marked scheduled.

## Closing
Either participant can complete an accepted mentorship (confirmation dialog, optional outcome summary). Status becomes `completed`, future scheduled sessions are cancelled (slots released), the other person is notified, and nothing is deleted. Chat history stays readable and sending is blocked.

## Migration
`app/database/workspace_migration.py`, called from `init_database()` on backend start: new tables come from `create_all`, then it adds the three columns when missing, widens the PostgreSQL check constraint when it lacks `completed`, and backfills sessions for bookings that have none. Idempotent and additive. **Restart the backend once after pulling.**

## API
All under `/api/mentorships/{id}`:
`GET /workspace`, `GET|POST /sessions`, `GET|PATCH /sessions/{sid}`, `POST /sessions/{sid}/cancel|complete`, `POST /sessions/{sid}/notes`, `GET /notes`, `PATCH /notes/{nid}`, `GET|POST /goals`, `PATCH /goals/{gid}`, `GET /goals/{gid}/history`, `GET|POST /action-items`, `PATCH /action-items/{iid}`, `GET /progress`, `GET /timeline`, `POST /close`.

Modified: `GET /api/chat/conversations` now includes completed mentorships and a `mentorship_status` field; `POST /api/bookings` and `PATCH /api/bookings/{id}/cancel` keep the linked session in step; mentorship responses may now report `completed`.

## Frontend
Routes `/mentorships/:id` (Overview), `sessions`, `sessions/:sessionId`, `notes`, `goals`, `progress`, under `src/pages/workspace/`. Entry: "Open workspace" on accepted mentorships in My mentorships and the Mentor dashboard.

## Additions after the first release
- **Why this mentor (`match_reasons`).** `GET /api/matches/me` items carry an extra descriptive list (shared skills, same domain or path, goal words that also appear in the mentor's profile). It is produced by `app/services/match_explanation.py` from the two profiles only. Ranking, embeddings and `similarity_score` are unchanged, and a mentor can rank highly with an empty list because the model also matches on meaning, not only on shared words. The percentage remains a ranking signal, not an accuracy figure.
- **Feedback on closure.** `mentorship_feedback` (one 1 to 5 rating and optional comment per participant, only after completion). `GET|POST /api/mentorships/{id}/feedback`. The other participant never sees it. Administrators see only the count and average (`metrics.match_feedback` on `/api/admin/dashboard`). This is the first real outcome signal for evaluating the recommender; it is not used to change ranking.
- **Reminders.** Created on demand when notifications or the bell count are read (`app/services/reminders.py`): a session starting within 24 hours, and an open action item past its due date. One reminder per member per item.
- **Summary.** `GET /api/mentorships/summary` returns open and overdue action items and the next session for each accepted mentorship the caller is in; shown on the mentee and mentor list pages.
- **Write limit.** 200 workspace writes per member per hour, then 429.
- **Summary export.** "Download summary (PDF)" uses the browser print dialog with a print stylesheet; private notes are not part of that page.
- **Local time.** Session times stay in EAT; a viewer outside East Africa also sees their own time.
- **Calendar colours.** Available slots are green and booked slots are blue.

## Known limits
Tests run on SQLite. The migration has been run against the real development PostgreSQL database, which has no status CHECK constraint on `mentorships` (it predates that rule), so completing a mentorship works there; a fresh install gets the widened constraint from the model. No Alembic yet.

## Not included
No calendar or video integration (links are stored as references), no file attachments, no search endpoint.
