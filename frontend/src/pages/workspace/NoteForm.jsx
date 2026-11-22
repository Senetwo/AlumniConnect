import { useState } from "react";
import { Lock, Users } from "lucide-react";
import { apiRequest } from "../../services/api";
import { Field, Modal } from "./ui";
import { NOTE_SECTIONS } from "./format";

export function NoteBody({ note }) {
  return (
    <dl className="ws-note-body">
      {NOTE_SECTIONS.filter(([key]) => note[key]).map(([key, text]) => (
        <div key={key}><dt>{text}</dt><dd>{note[key]}</dd></div>
      ))}
    </dl>
  );
}

export function VisibilityChip({ note }) {
  return note.visibility === "private"
    ? <span className="ws-chip is-private"><Lock size={12} aria-hidden="true" />Private, only you</span>
    : <span className="ws-chip is-shared"><Users size={12} aria-hidden="true" />Shared with both</span>;
}

// The author must choose shared or private; nothing is selected by default.
export default function NoteForm({ base, session, note = null, onClose, onSaved }) {
  const [form, setForm] = useState({
    visibility: note?.visibility ?? "",
    ...Object.fromEntries(NOTE_SECTIONS.map(([key]) => [key, note?.[key] ?? ""])),
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const set = (name) => (event) => setForm((current) => ({ ...current, [name]: event.target.value }));

  async function submit(event) {
    event.preventDefault();
    if (!form.visibility) { setError("Choose who can see this note before saving."); return; }
    setBusy(true); setError("");
    try {
      await apiRequest(note ? `${base}/notes/${note.id}` : `${base}/sessions/${session.id}/notes`, { method: note ? "PATCH" : "POST", body: JSON.stringify(form) });
      await onSaved();
    } catch (err) { setError(err.message || "Could not save the note."); setBusy(false); }
  }

  return (
    <Modal title={note ? "Edit meeting note" : `Meeting note: ${session.title}`} onClose={onClose} wide>
      <form className="register-form" onSubmit={submit}>
        {error && <div className="page-alert" role="alert">{error}</div>}
        <fieldset className="ws-visibility">
          <legend>Who can see this note?</legend>
          <label className={form.visibility === "shared" ? "is-selected" : ""}>
            <input type="radio" name="visibility" value="shared" checked={form.visibility === "shared"} onChange={set("visibility")} />
            <span><strong><Users size={14} aria-hidden="true" /> Shared</strong>Both of you can read it.</span>
          </label>
          <label className={form.visibility === "private" ? "is-selected" : ""}>
            <input type="radio" name="visibility" value="private" checked={form.visibility === "private"} onChange={set("visibility")} />
            <span><strong><Lock size={14} aria-hidden="true" /> Private</strong>Only you can read or edit it.</span>
          </label>
        </fieldset>
        {NOTE_SECTIONS.map(([key, text]) => (
          <Field key={key} id={`n-${key}`} label={text}><textarea id={`n-${key}`} rows={2} maxLength={4000} value={form[key]} onChange={set(key)} /></Field>
        ))}
        <p className="ws-hint">Add action items from the session page so they appear in the shared task list.</p>
        <div className="ws-form-actions">
          <button type="button" className="btn btn-outline" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" disabled={busy}>{busy ? "Saving…" : "Save note"}</button>
        </div>
      </form>
    </Modal>
  );
}
