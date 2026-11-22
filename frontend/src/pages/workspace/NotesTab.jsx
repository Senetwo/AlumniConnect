import { useCallback, useEffect, useState } from "react";
import { Link, useOutletContext } from "react-router-dom";
import { FileText } from "lucide-react";
import { FilterTabs } from "../../components/dashboard";
import { apiRequest } from "../../services/api";
import { initials } from "../../utils/format";
import NoteForm, { NoteBody, VisibilityChip } from "./NoteForm";
import { Empty, Loading } from "./ui";
import { formatDate } from "./format";

export default function NotesTab() {
  const { workspace, reload, base } = useOutletContext();
  const [notes, setNotes] = useState(null);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");
  const [editing, setEditing] = useState(null);

  const load = useCallback(async () => {
    try { setNotes(await apiRequest(`${base}/notes`)); setError(""); }
    catch (err) { setError(err.message || "Unable to load meeting notes."); }
  }, [base]);
  useEffect(() => { queueMicrotask(() => { void load(); }); }, [load]);

  const visible = (notes ?? []).filter((note) => filter === "all" || note.visibility === filter);
  const count = (kind) => (notes ?? []).filter((note) => kind === "all" || note.visibility === kind).length;

  return (
    <div className="ws-stack">
      <div className="pg-section-title"><h2>Meeting notes</h2></div>
      <p className="ws-muted">Shared notes are visible to both of you. Private notes are visible only to their author, and never appear in the other person's workspace, progress or timeline.</p>
      {error && <div className="page-alert" role="alert">{error}</div>}
      {!notes && !error && <Loading text="Loading notes" />}
      {notes && (
        <>
          <FilterTabs label="Filter notes" value={filter} onChange={setFilter} options={[
            { id: "all", label: "All", count: count("all") },
            { id: "shared", label: "Shared", count: count("shared") },
            { id: "private", label: "My private notes", count: count("private") },
          ]} />
          {visible.length === 0
            ? <Empty icon={FileText} title="No notes here yet">Open a session and choose Add note. You pick shared or private every time.</Empty>
            : visible.map((note) => (
              <article className="pg-card ws-note" key={note.id}>
                <div className="ws-row">
                  <div className="ws-author"><span className="pg-avatar" aria-hidden="true">{initials(note.author_name)}</span><span>
                    <strong><Link to={`../sessions/${note.session_id}`}>{note.session_title || "Session"}</Link></strong>
                    <small>{note.is_mine ? "You" : note.author_name} · {formatDate(note.created_at)}</small>
                  </span></div>
                  <VisibilityChip note={note} />
                </div>
                <NoteBody note={note} />
                {note.is_mine && workspace.is_writable && <div className="pg-actions"><button type="button" className="btn btn-outline ws-small" onClick={() => setEditing(note)}>Edit note</button></div>}
              </article>
            ))}
        </>
      )}
      {editing && <NoteForm base={base} session={{ id: editing.session_id, title: editing.session_title }} note={editing} onClose={() => setEditing(null)} onSaved={async () => { setEditing(null); await Promise.all([load(), reload()]); }} />}
    </div>
  );
}
