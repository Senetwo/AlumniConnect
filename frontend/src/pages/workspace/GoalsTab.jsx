import { useCallback, useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { Flag, History, Pencil, Plus } from "lucide-react";
import { FilterTabs } from "../../components/dashboard";
import { apiRequest } from "../../services/api";
import ActionItems from "./ActionItems";
import { Empty, Field, Loading, Modal, StatusChip } from "./ui";
import { formatDate, label } from "./format";

const STATUSES = ["not_started", "in_progress", "completed", "on_hold"];

function GoalForm({ workspace, base, goal = null, onClose, onSaved }) {
  const editing = goal !== null;
  const [form, setForm] = useState({
    title: goal?.title ?? "", description: goal?.description ?? "", target_date: goal?.target_date ?? "",
    assignee_id: goal?.assignee_id ? String(goal.assignee_id) : "", status: goal?.status ?? "not_started",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const set = (name) => (event) => setForm((current) => ({ ...current, [name]: event.target.value }));

  async function submit(event) {
    event.preventDefault(); setBusy(true); setError("");
    const body = {
      title: form.title, description: form.description || null, status: form.status,
      target_date: form.target_date || null, assignee_id: form.assignee_id ? Number(form.assignee_id) : null,
    };
    if (editing) {
      body.clear_target_date = !form.target_date;
      body.clear_assignee = !form.assignee_id;
      if (!form.description) body.description = "";
    }
    try {
      await apiRequest(editing ? `${base}/goals/${goal.id}` : `${base}/goals`, { method: editing ? "PATCH" : "POST", body: JSON.stringify(body) });
      await onSaved();
    } catch (err) { setError(err.message || "Could not save the goal."); setBusy(false); }
  }

  return (
    <Modal title={editing ? "Edit goal" : "New goal"} onClose={onClose} wide>
      <form className="register-form" onSubmit={submit}>
        {error && <div className="page-alert" role="alert">{error}</div>}
        <Field id="g-title" label="Goal"><input id="g-title" value={form.title} onChange={set("title")} minLength={3} maxLength={160} required placeholder="e.g. Prepare for the type-rating interview" /></Field>
        <Field id="g-desc" label="Description (optional)"><textarea id="g-desc" rows={3} value={form.description} onChange={set("description")} maxLength={2000} /></Field>
        <div className="register-grid">
          <Field id="g-date" label="Target date (optional)"><input id="g-date" type="date" value={form.target_date} onChange={set("target_date")} /></Field>
          <Field id="g-who" label="Responsible">
            <select id="g-who" value={form.assignee_id} onChange={set("assignee_id")}>
              <option value="">Both of us</option>
              <option value={workspace.mentor.user_id}>{workspace.mentor.full_name} (mentor)</option>
              <option value={workspace.mentee.user_id}>{workspace.mentee.full_name} (mentee)</option>
            </select>
          </Field>
          <Field id="g-status" label="Status">
            <select id="g-status" value={form.status} onChange={set("status")}>{STATUSES.map((s) => <option key={s} value={s}>{label(s)}</option>)}</select>
          </Field>
        </div>
        <div className="ws-form-actions">
          <button type="button" className="btn btn-outline" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" disabled={busy}>{busy ? "Saving…" : editing ? "Save changes" : "Add goal"}</button>
        </div>
      </form>
    </Modal>
  );
}

function GoalCard({ goal, workspace, base, onChanged, onEdit }) {
  const [history, setHistory] = useState(null);
  const [error, setError] = useState("");
  const writable = workspace.is_writable;

  async function changeStatus(event) {
    setError("");
    try { await apiRequest(`${base}/goals/${goal.id}`, { method: "PATCH", body: JSON.stringify({ status: event.target.value }) }); await onChanged(); }
    catch (err) { setError(err.message || "Could not update the goal."); }
  }
  async function toggleHistory() {
    if (history) { setHistory(null); return; }
    try { setHistory(await apiRequest(`${base}/goals/${goal.id}/history`)); }
    catch (err) { setError(err.message || "Could not load the history."); }
  }

  return (
    <article className="pg-card ws-goal">
      <div className="ws-row">
        <div>
          <h3>{goal.title}</h3>
          <small>Responsible: {goal.assignee_name}{goal.target_date ? ` · target ${formatDate(goal.target_date)}${goal.is_overdue ? " (past)" : ""}` : ""}</small>
        </div>
        <StatusChip value={goal.status} />
      </div>
      {goal.description && <p className="ws-prewrap">{goal.description}</p>}
      {error && <div className="page-alert" role="alert">{error}</div>}
      <div className="pg-actions">
        {writable && (
          <label className="ws-inline-select">Status
            <select value={goal.status} onChange={changeStatus}>{STATUSES.map((s) => <option key={s} value={s}>{label(s)}</option>)}</select>
          </label>
        )}
        {writable && <button type="button" className="btn btn-outline ws-small" onClick={() => onEdit(goal)}><Pencil size={14} aria-hidden="true" />Edit</button>}
        <button type="button" className="btn btn-outline ws-small" onClick={toggleHistory} aria-expanded={history !== null}><History size={14} aria-hidden="true" />{history ? "Hide history" : "History"}</button>
      </div>
      {history && (
        <ol className="ws-updates">
          {history.map((event) => <li key={event.id}><span>{event.summary}{event.old_value ? ` (${label(event.old_value)} → ${label(event.new_value)})` : ""}</span><small>{event.actor_name} · {formatDate(event.created_at)}</small></li>)}
        </ol>
      )}
      <ActionItems
        title="Action items for this goal" items={goal.action_items} workspace={workspace} base={base} onChanged={onChanged}
        goalId={goal.id} empty="No action items linked to this goal."
      />
    </article>
  );
}

export default function GoalsTab() {
  const { workspace, reload, base } = useOutletContext();
  const [goals, setGoals] = useState(null);
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState(null); // {} for new, a goal for edit
  const [itemFilter, setItemFilter] = useState("open");

  const load = useCallback(async () => {
    try {
      const [goalList, itemList] = await Promise.all([apiRequest(`${base}/goals`), apiRequest(`${base}/action-items`)]);
      setGoals(goalList); setItems(itemList); setError("");
    } catch (err) { setError(err.message || "Unable to load goals."); }
  }, [base]);
  useEffect(() => { queueMicrotask(() => { void load(); }); }, [load]);

  const refresh = useCallback(async () => { await Promise.all([load(), reload()]); }, [load, reload]);
  const writable = workspace.is_writable;
  const shownItems = items.filter((item) => itemFilter === "all" || item.status === itemFilter);

  return (
    <div className="ws-stack">
      <div className="pg-section-title">
        <h2>Goals</h2>
        {writable && <button type="button" className="btn btn-primary" onClick={() => setForm({})}><Plus size={16} aria-hidden="true" />New goal</button>}
      </div>
      {error && <div className="page-alert" role="alert">{error}</div>}
      {!goals && !error && <Loading text="Loading goals" />}
      {goals && goals.length === 0 && (
        <Empty icon={Flag} title="No goals set yet">{writable ? "Agree on what you want to achieve together. Goals are visible to both of you." : "No goals were set in this mentorship."}</Empty>
      )}
      {goals && goals.map((goal) => (
        <GoalCard key={goal.id} goal={goal} workspace={workspace} base={base} onChanged={refresh} onEdit={setForm} />
      ))}

      {goals && (
        <section className="ws-block" aria-labelledby="all-items">
          <h2 id="all-items">All action items</h2>
          <FilterTabs label="Filter action items" value={itemFilter} onChange={setItemFilter} options={[
            { id: "open", label: "Outstanding", count: items.filter((i) => i.status === "open").length },
            { id: "completed", label: "Completed", count: items.filter((i) => i.status === "completed").length },
            { id: "all", label: "All", count: items.length },
          ]} />
          <div>
            <ActionItems title="Tasks" items={shownItems} workspace={workspace} base={base} onChanged={refresh} goals={goals} empty={itemFilter === "open" ? "Nothing outstanding." : "Nothing here."} />
          </div>
        </section>
      )}

      {form && <GoalForm workspace={workspace} base={base} goal={form.id ? form : null} onClose={() => setForm(null)} onSaved={async () => { setForm(null); await refresh(); }} />}
    </div>
  );
}
