import { useState } from "react";
import { CalendarClock, Plus } from "lucide-react";
import { apiRequest } from "../../services/api";
import { Field, Modal } from "./ui";
import { formatDate } from "./format";

// Checklist of action items with an "add" form. Used on the goals page and the session page.
export default function ActionItems({ items, workspace, base, onChanged, goalId = null, sessionId = null, goals = [], title = "Action items", empty }) {
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);
  const writable = workspace.is_writable;

  async function toggle(item) {
    setBusyId(item.id); setError("");
    try {
      await apiRequest(`${base}/action-items/${item.id}`, { method: "PATCH", body: JSON.stringify({ status: item.status === "open" ? "completed" : "open" }) });
      await onChanged();
    } catch (err) { setError(err.message || "Could not update the action item."); }
    finally { setBusyId(null); }
  }

  return (
    <section className="ws-block" aria-label={title}>
      <div className="ws-block-head">
        <h3>{title}</h3>
        {writable && <button type="button" className="btn btn-outline ws-small" onClick={() => setAdding(true)}><Plus size={15} aria-hidden="true" />Add</button>}
      </div>
      {error && <div className="page-alert" role="alert">{error}</div>}
      {items.length === 0 ? <p className="ws-muted">{empty || "No action items yet."}</p> : (
        <ul className="ws-checklist">
          {items.map((item) => (
            <li key={item.id} className={item.status === "completed" ? "is-done" : ""}>
              <input
                type="checkbox" id={`ai-${item.id}`} checked={item.status === "completed"}
                disabled={!writable || busyId === item.id} onChange={() => toggle(item)}
              />
              <label htmlFor={`ai-${item.id}`}>
                <span>{item.description}</span>
                <small>
                  {item.assigned_to_name}
                  {item.due_date && <> · <CalendarClock size={12} aria-hidden="true" /> {item.status === "open" && item.is_overdue ? "Overdue, " : "Due "}{formatDate(item.due_date)}</>}
                  {item.status === "completed" && item.completed_at && <> · done {formatDate(item.completed_at)}</>}
                </small>
              </label>
            </li>
          ))}
        </ul>
      )}
      {adding && (
        <ActionItemForm
          workspace={workspace} base={base} goalId={goalId} sessionId={sessionId} goals={goals}
          onClose={() => setAdding(false)} onSaved={async () => { setAdding(false); await onChanged(); }}
        />
      )}
    </section>
  );
}

function ActionItemForm({ workspace, base, goalId, sessionId, goals, onClose, onSaved }) {
  const [form, setForm] = useState({ description: "", assigned_to_id: String(workspace.viewer.user_id), due_date: "", goal_id: goalId ? String(goalId) : "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const set = (name) => (event) => setForm((current) => ({ ...current, [name]: event.target.value }));

  async function submit(event) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      await apiRequest(`${base}/action-items`, {
        method: "POST",
        body: JSON.stringify({
          description: form.description, assigned_to_id: Number(form.assigned_to_id),
          due_date: form.due_date || null, goal_id: form.goal_id ? Number(form.goal_id) : null, session_id: sessionId,
        }),
      });
      await onSaved();
    } catch (err) { setError(err.message || "Could not save the action item."); setBusy(false); }
  }

  return (
    <Modal title="New action item" onClose={onClose}>
      <form className="register-form" onSubmit={submit}>
        {error && <div className="page-alert" role="alert">{error}</div>}
        <Field id="ai-desc" label="What needs to be done?"><input id="ai-desc" value={form.description} onChange={set("description")} minLength={3} maxLength={500} required /></Field>
        <div className="register-grid">
          <Field id="ai-who" label="Responsible">
            <select id="ai-who" value={form.assigned_to_id} onChange={set("assigned_to_id")}>
              <option value={workspace.mentor.user_id}>{workspace.mentor.full_name} (mentor)</option>
              <option value={workspace.mentee.user_id}>{workspace.mentee.full_name} (mentee)</option>
            </select>
          </Field>
          <Field id="ai-due" label="Due date (optional)"><input id="ai-due" type="date" value={form.due_date} onChange={set("due_date")} /></Field>
        </div>
        {!goalId && goals.length > 0 && (
          <Field id="ai-goal" label="Linked goal (optional)">
            <select id="ai-goal" value={form.goal_id} onChange={set("goal_id")}>
              <option value="">No goal</option>
              {goals.map((goal) => <option key={goal.id} value={goal.id}>{goal.title}</option>)}
            </select>
          </Field>
        )}
        <div className="ws-form-actions">
          <button type="button" className="btn btn-outline" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" disabled={busy}>{busy ? "Saving…" : "Add action item"}</button>
        </div>
      </form>
    </Modal>
  );
}
