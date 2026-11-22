import { useCallback, useEffect, useState } from "react";
import { Link, useOutletContext } from "react-router-dom";
import { CalendarClock, MapPin, Plus, Video } from "lucide-react";
import { apiRequest } from "../../services/api";
import SessionForm from "./SessionForm";
import { useSessionActions } from "./useSessionActions";
import { DateTile } from "../../components/dashboard";
import { Empty, Loading, StatusChip } from "./ui";
import { formatWhen } from "./format";

export function SessionCard({ session, writable, onEdit, onCancel, onComplete, linkTo }) {
  const started = new Date(session.scheduled_at) <= new Date();
  return (
    <article className="pg-card ws-session">
      <DateTile iso={session.scheduled_at} />
      <div className="ws-session-body">
      <div className="ws-row">
        <div>
          <h3>{linkTo ? <Link to={linkTo}>{session.title}</Link> : session.title}</h3>
          <small><CalendarClock size={13} aria-hidden="true" /> {formatWhen(session.scheduled_at)} · {session.duration_minutes} min</small>
        </div>
        <StatusChip value={session.status} />
      </div>
      <p className="ws-meta">
        {session.meeting_type === "virtual" ? <><Video size={14} aria-hidden="true" />Virtual</> : <><MapPin size={14} aria-hidden="true" />In person</>}
        {session.meeting_link && <> · <a href={session.meeting_link} target="_blank" rel="noopener noreferrer">Meeting link</a></>}
        {session.location && <> · {session.location}</>}
      </p>
      {session.status === "cancelled" && session.cancel_reason && <p className="ws-muted">Cancelled: {session.cancel_reason}</p>}
      <div className="pg-actions">
        {linkTo && <Link to={linkTo} className="btn btn-outline">Details & notes</Link>}
        {writable && session.status === "scheduled" && <button type="button" className="btn btn-outline" onClick={() => onEdit(session)}>Edit</button>}
        {writable && session.status === "scheduled" && started && <button type="button" className="btn btn-primary" onClick={() => onComplete(session)}>Mark completed</button>}
        {writable && session.status === "scheduled" && !(session.from_booking && started) && <button type="button" className="btn btn-outline ws-danger" onClick={() => onCancel(session)}>Cancel session</button>}
      </div>
      </div>
    </article>
  );
}

export default function SessionsTab() {
  const { workspace, reload, base } = useOutletContext();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    try { setData(await apiRequest(`${base}/sessions`)); setError(""); }
    catch (err) { setError(err.message || "Unable to load sessions."); }
  }, [base]);
  useEffect(() => { queueMicrotask(() => { void load(); }); }, [load]);

  const refresh = useCallback(async () => { await Promise.all([load(), reload()]); }, [load, reload]);
  const actions = useSessionActions(base, refresh);
  const writable = workspace.is_writable;

  return (
    <div className="ws-stack">
      <div className="pg-section-title">
        <h2>Sessions</h2>
        {writable && <button type="button" className="btn btn-primary" onClick={() => setCreating(true)}><Plus size={16} aria-hidden="true" />Schedule session</button>}
      </div>
      {(error || actions.error) && <div className="page-alert" role="alert">{error || actions.error}</div>}
      {!data && !error && <Loading text="Loading sessions" />}
      {data && (
        <>
          <section className="ws-block" aria-labelledby="up-title">
            <h3 id="up-title">Upcoming</h3>
            {data.upcoming.length === 0
              ? <Empty icon={CalendarClock} title="No upcoming sessions">{writable ? "Schedule a session, or book one of the mentor's open slots from My mentorships." : "No sessions were scheduled."}</Empty>
              : data.upcoming.map((session) => <SessionCard key={session.id} session={session} writable={writable} linkTo={`${session.id}`} {...actions} />)}
          </section>
          <section className="ws-block" aria-labelledby="past-title">
            <h3 id="past-title">Past and cancelled</h3>
            {data.past.length === 0
              ? <p className="ws-muted">Completed and cancelled sessions will appear here.</p>
              : data.past.map((session) => <SessionCard key={session.id} session={session} writable={writable} linkTo={`${session.id}`} {...actions} />)}
          </section>
        </>
      )}
      {creating && <SessionForm base={base} onClose={() => setCreating(false)} onSaved={async () => { setCreating(false); await refresh(); }} />}
      {actions.dialogs}
    </div>
  );
}
