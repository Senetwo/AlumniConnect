import { useCallback, useEffect, useState } from "react";
import { Link, useOutletContext, useParams } from "react-router-dom";
import { ArrowLeft, CalendarClock, FileText, MapPin, Pencil, Plus, Video } from "lucide-react";
import { apiRequest } from "../../services/api";
import { initials } from "../../utils/format";
import ActionItems from "./ActionItems";
import NoteForm, { NoteBody, VisibilityChip } from "./NoteForm";
import { useSessionActions } from "./useSessionActions";
import { Empty, Loading, StatusChip } from "./ui";
import { formatDate, formatWhen } from "./format";

export default function SessionDetailPage() {
  const { sessionId } = useParams();
  const { workspace, reload, base } = useOutletContext();
  const [session, setSession] = useState(null);
  const [error, setError] = useState("");
  const [noteForm, setNoteForm] = useState(null); // {} for a new note, or the note being edited

  const load = useCallback(async () => {
    try { setSession(await apiRequest(`${base}/sessions/${sessionId}`)); setError(""); }
    catch (err) { setError(err.message || "Unable to load this session."); }
  }, [base, sessionId]);
  useEffect(() => { queueMicrotask(() => { void load(); }); }, [load]);

  const refresh = useCallback(async () => { await Promise.all([load(), reload()]); }, [load, reload]);
  const actions = useSessionActions(base, refresh);
  const writable = workspace.is_writable;

  if (error) return <div className="ws-stack"><Link to=".." relative="path" className="ws-back"><ArrowLeft size={16} />Sessions</Link><div className="page-alert" role="alert">{error}</div></div>;
  if (!session) return <Loading text="Loading session" />;

  const started = new Date(session.scheduled_at) <= new Date();
  const canNote = writable && session.status !== "cancelled";

  return (
    <div className="ws-stack">
      <Link to=".." relative="path" className="ws-back"><ArrowLeft size={16} aria-hidden="true" />All sessions</Link>
      {actions.error && <div className="page-alert" role="alert">{actions.error}</div>}

      <section className="pg-card ws-session-head">
        <div className="ws-row">
          <div>
            <h2>{session.title}</h2>
            <small><CalendarClock size={13} aria-hidden="true" /> {formatWhen(session.scheduled_at)} · {session.duration_minutes} min</small>
          </div>
          <StatusChip value={session.status} />
        </div>
        <p className="ws-meta">
          {session.meeting_type === "virtual" ? <><Video size={14} aria-hidden="true" />Virtual</> : <><MapPin size={14} aria-hidden="true" />In person</>}
          {session.meeting_link && <> · <a href={session.meeting_link} target="_blank" rel="noopener noreferrer">Meeting link</a></>}
          {session.location && <> · {session.location}</>}
        </p>
        {session.description && <p>{session.description}</p>}
        {session.status === "cancelled" && session.cancel_reason && <p className="ws-muted">Cancelled: {session.cancel_reason}</p>}
        <div className="ws-participants">
          {session.participants.map((person) => <span key={person.user_id} className="ws-chip">{person.full_name} · {person.role}</span>)}
        </div>
        {writable && session.status === "scheduled" && (
          <div className="pg-actions">
            <button type="button" className="btn btn-outline" onClick={() => actions.onEdit(session)}><Pencil size={15} aria-hidden="true" />Edit</button>
            {started && <button type="button" className="btn btn-primary" onClick={() => actions.onComplete(session)}>Mark completed</button>}
            {!(session.from_booking && started) && <button type="button" className="btn btn-outline ws-danger" onClick={() => actions.onCancel(session)}>Cancel session</button>}
          </div>
        )}
      </section>

      <section className="ws-block" aria-labelledby="agenda-title">
        <h3 id="agenda-title">Agenda</h3>
        {session.agenda ? <p className="pg-card ws-prewrap">{session.agenda}</p> : <p className="ws-muted">No agenda was added.</p>}
      </section>

      <section className="ws-block" aria-labelledby="notes-title">
        <div className="ws-block-head">
          <h3 id="notes-title">Meeting notes</h3>
          {canNote && <button type="button" className="btn btn-outline ws-small" onClick={() => setNoteForm({})}><Plus size={15} aria-hidden="true" />Add note</button>}
        </div>
        {session.notes.length === 0
          ? <Empty icon={FileText} title="No notes for this session">{canNote ? "Add a shared note for both of you, or a private note only you can see." : "Notes were not recorded for this session."}</Empty>
          : session.notes.map((note) => (
            <article className="pg-card ws-note" key={note.id}>
              <div className="ws-row">
                <div className="ws-author"><span className="pg-avatar" aria-hidden="true">{initials(note.author_name)}</span><span><strong>{note.is_mine ? "You" : note.author_name}</strong><small>{formatDate(note.created_at)}{note.updated_at !== note.created_at ? ` · edited ${formatDate(note.updated_at)}` : ""}</small></span></div>
                <VisibilityChip note={note} />
              </div>
              <NoteBody note={note} />
              {note.is_mine && writable && <div className="pg-actions"><button type="button" className="btn btn-outline ws-small" onClick={() => setNoteForm(note)}>Edit note</button></div>}
            </article>
          ))}
      </section>

      <ActionItems
        title="Action items from this session" items={session.action_items} workspace={workspace} base={base} onChanged={refresh}
        sessionId={session.id} empty="No action items were set in this session."
      />

      {noteForm && (
        <NoteForm
          base={base} session={session} note={noteForm.id ? noteForm : null}
          onClose={() => setNoteForm(null)} onSaved={async () => { setNoteForm(null); await refresh(); }}
        />
      )}
      {actions.dialogs}
    </div>
  );
}
