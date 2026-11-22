import { useState } from "react";
import { apiRequest } from "../../services/api";
import { Field, Modal } from "./ui";
import { fromEatInput, toEatInput } from "./format";

// Create (no `session`) or edit a session. Times are entered in East Africa Time.
export default function SessionForm({ base, session = null, onClose, onSaved }) {
  const editing = session !== null;
  const timeLocked = editing && session.from_booking;
  const [form, setForm] = useState({
    title: session?.title ?? "",
    description: session?.description ?? "",
    when: session ? toEatInput(session.scheduled_at) : "",
    duration_minutes: String(session?.duration_minutes ?? 60),
    meeting_type: session?.meeting_type ?? "virtual",
    location: session?.location ?? "",
    meeting_link: session?.meeting_link ?? "",
    agenda: session?.agenda ?? "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const set = (name) => (event) => setForm((current) => ({ ...current, [name]: event.target.value }));

  async function submit(event) {
    event.preventDefault(); setBusy(true); setError("");
    const body = {
      title: form.title, description: form.description || null, agenda: form.agenda || null,
      meeting_type: form.meeting_type,
      location: form.meeting_type === "in_person" ? form.location || null : null,
      meeting_link: form.meeting_type === "virtual" ? form.meeting_link || null : null,
    };
    if (!timeLocked) {
      body.scheduled_at = fromEatInput(form.when);
      body.duration_minutes = Number(form.duration_minutes);
    }
    try {
      await apiRequest(editing ? `${base}/sessions/${session.id}` : `${base}/sessions`, { method: editing ? "PATCH" : "POST", body: JSON.stringify(body) });
      await onSaved();
    } catch (err) { setError(err.message || "Could not save the session."); setBusy(false); }
  }

  return (
    <Modal title={editing ? "Edit session" : "Schedule a session"} onClose={onClose} wide>
      <form className="register-form" onSubmit={submit}>
        {error && <div className="page-alert" role="alert">{error}</div>}
        <Field id="s-title" label="Title"><input id="s-title" value={form.title} onChange={set("title")} minLength={3} maxLength={160} required /></Field>
        <div className="register-grid">
          <Field id="s-when" label="Date and start time (EAT)" hint={timeLocked ? "This time comes from a booked slot. Cancel and book another slot to change it." : "East Africa Time"}>
            <input id="s-when" type="datetime-local" value={form.when} onChange={set("when")} required disabled={timeLocked} />
          </Field>
          <Field id="s-dur" label="Duration (minutes)">
            <input id="s-dur" type="number" min={5} max={480} step={5} value={form.duration_minutes} onChange={set("duration_minutes")} required disabled={timeLocked} />
          </Field>
          <Field id="s-type" label="Meeting type">
            <select id="s-type" value={form.meeting_type} onChange={set("meeting_type")}>
              <option value="virtual">Virtual</option>
              <option value="in_person">In person</option>
            </select>
          </Field>
          {form.meeting_type === "virtual"
            ? <Field id="s-link" label="Meeting link (optional)" hint="Saved as a reference only; nothing is joined from here."><input id="s-link" type="url" placeholder="https://" value={form.meeting_link} onChange={set("meeting_link")} maxLength={1000} /></Field>
            : <Field id="s-loc" label="Location (optional)"><input id="s-loc" value={form.location} onChange={set("location")} maxLength={255} /></Field>}
        </div>
        <Field id="s-desc" label="Description (optional)"><textarea id="s-desc" rows={2} value={form.description} onChange={set("description")} maxLength={2000} /></Field>
        <Field id="s-agenda" label="Agenda (optional)"><textarea id="s-agenda" rows={4} value={form.agenda} onChange={set("agenda")} maxLength={4000} placeholder="Topics to cover, one per line" /></Field>
        <div className="ws-form-actions">
          <button type="button" className="btn btn-outline" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" disabled={busy}>{busy ? "Saving…" : editing ? "Save changes" : "Schedule session"}</button>
        </div>
      </form>
    </Modal>
  );
}
