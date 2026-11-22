import { useState } from "react";
import { Link, useOutletContext } from "react-router-dom";
import { CalendarClock, CheckCircle2, Download, Flag, ListChecks, Lock } from "lucide-react";
import { apiRequest } from "../../services/api";
import { initials } from "../../utils/format";
import { careerDomains } from "../../data/careers";
import Feedback from "./Feedback";
import { ConfirmDialog, Empty, StatusChip } from "./ui";
import { formatDate, formatWhen } from "./format";

function Party({ person }) {
  return (
    <article className="pg-card ws-party">
      <span className="pg-avatar" aria-hidden="true">{initials(person.full_name)}</span>
      <div>
        <small className={`is-${person.role}`}>{person.role === "mentor" ? "Mentor" : "Mentee"}</small>
        <h3>{person.full_name}</h3>
        <p>{[person.career_path, careerDomains.find((domain) => domain.id === person.career_domain)?.name || person.career_domain].filter(Boolean).join(" · ") || "Profile not completed"}</p>
        {person.experience && <p className="ws-muted">{person.experience} experience</p>}
      </div>
    </article>
  );
}

export default function OverviewTab() {
  const { workspace: ws, reload, base } = useOutletContext();
  const [closing, setClosing] = useState(false);
  const [summary, setSummary] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const { progress } = ws;

  async function close() {
    setBusy(true); setError("");
    try {
      await apiRequest(`${base}/close`, { method: "POST", body: JSON.stringify({ outcome_summary: summary }) });
      setClosing(false);
      await reload();
    } catch (err) { setError(err.message || "Could not close the mentorship."); setClosing(false); }
    finally { setBusy(false); }
  }

  return (
    <div className="ws-stack">
      {error && <div className="page-alert" role="alert">{error}</div>}

      {ws.status === "completed" && (
        <section className="pg-card ws-closed" aria-label="Mentorship completed">
          <CheckCircle2 size={22} aria-hidden="true" />
          <div>
            <h2>Mentorship completed</h2>
            <p>Closed {formatDate(ws.closed_at)}{ws.closed_by_name ? ` by ${ws.closed_by_name}` : ""}. Sessions, notes, goals and action items are kept below as a record.</p>
            {ws.outcome_summary && <blockquote className="pg-quote"><span>Outcome</span><p>{ws.outcome_summary}</p></blockquote>}
          </div>
        </section>
      )}

      <div className="ws-print-title">
        <h1>Mentorship summary</h1>
        <p>{ws.mentor.full_name} (mentor) and {ws.mentee.full_name} (mentee). Started {formatDate(ws.started_at)}. Printed {formatDate(new Date().toISOString())}.</p>
      </div>
      {ws.status === "completed" && <Feedback base={base} />}

      <div className="ws-grid-2">
        <Party person={ws.mentor} />
        <Party person={ws.mentee} />
      </div>
      <p className="ws-muted ws-started">Started {formatDate(ws.started_at)}.</p>

      <section className="pg-stats" aria-label="At a glance">
        <article className="pg-card pg-stat"><span className="pg-stat-icon"><Flag size={20} aria-hidden="true" /></span><div><strong>{progress.goals.completed}/{progress.goals.total}</strong><span>Goals completed</span></div></article>
        <article className="pg-card pg-stat"><span className="pg-stat-icon"><ListChecks size={20} aria-hidden="true" /></span><div><strong>{progress.action_items.open}</strong><span>Open action items</span>{progress.action_items.overdue > 0 && <small>{progress.action_items.overdue} overdue</small>}</div></article>
        <article className="pg-card pg-stat"><span className="pg-stat-icon"><CalendarClock size={20} aria-hidden="true" /></span><div><strong>{progress.sessions.upcoming}</strong><span>Upcoming sessions</span></div></article>
        <article className="pg-card pg-stat"><span className="pg-stat-icon"><CheckCircle2 size={20} aria-hidden="true" /></span><div><strong>{progress.sessions.completed}</strong><span>Sessions completed</span></div></article>
      </section>

      {progress.needs_attention.length > 0 && (
        <section className="pg-card ws-attention" aria-label="Needs attention">
          <h2>Needs attention</h2>
          <ul>{progress.needs_attention.map((item) => <li key={`${item.type}-${item.entity_id}`}>{item.message}</li>)}</ul>
        </section>
      )}

      <div className="pg-layout">
        <div className="pg-main">
          <section className="ws-block" aria-labelledby="ov-goals">
            <div className="ws-block-head"><h2 id="ov-goals">Agreed goals</h2><Link to="goals" className="cm-link">Manage</Link></div>
            {ws.goals.length === 0 ? <Empty icon={Flag} title="No goals yet">Agree on one or two goals you want this mentorship to work towards.</Empty> : ws.goals.slice(0, 4).map((goal) => (
              <article className="pg-card ws-row" key={goal.id}>
                <div><h3>{goal.title}</h3><small>{goal.assignee_name} {goal.target_date ? `· target ${formatDate(goal.target_date)}` : ""}</small></div>
                <StatusChip value={goal.status} />
              </article>
            ))}
          </section>

          <section className="ws-block" aria-labelledby="ov-actions">
            <div className="ws-block-head"><h2 id="ov-actions">Outstanding action items</h2><Link to="goals" className="cm-link">Manage</Link></div>
            {ws.outstanding_action_items.length === 0 ? <p className="ws-muted">Nothing outstanding.</p> : (
              <ul className="pg-card ws-plain-list">
                {ws.outstanding_action_items.slice(0, 6).map((item) => (
                  <li key={item.id}><span>{item.description}</span><small>{item.assigned_to_name}{item.due_date ? ` · ${item.is_overdue ? "overdue " : "due "}${formatDate(item.due_date)}` : ""}</small></li>
                ))}
              </ul>
            )}
          </section>
        </div>

        <aside className="pg-aside" aria-label="Sessions and updates">
          <section className="ws-block">
            <div className="ws-block-head"><h2>Upcoming sessions</h2><Link to="sessions" className="cm-link">All</Link></div>
            {ws.upcoming_sessions.length === 0 ? <p className="ws-muted">No sessions scheduled.</p> : ws.upcoming_sessions.map((session) => (
              <Link key={session.id} to={`sessions/${session.id}`} className="pg-card ws-mini"><strong>{session.title}</strong><small>{formatWhen(session.scheduled_at)}</small></Link>
            ))}
          </section>
          <section className="ws-block">
            <h2>Recent sessions</h2>
            {ws.recent_sessions.length === 0 ? <p className="ws-muted">No completed sessions yet.</p> : ws.recent_sessions.map((session) => (
              <Link key={session.id} to={`sessions/${session.id}`} className="pg-card ws-mini"><strong>{session.title}</strong><small>{formatWhen(session.scheduled_at)}</small></Link>
            ))}
          </section>
          <section className="ws-block">
            <div className="ws-block-head"><h2>Recent updates</h2><Link to="progress" className="cm-link">History</Link></div>
            <ol className="ws-updates">
              {ws.recent_updates.map((event) => <li key={`${event.event_type}-${event.id ?? "m"}`}><span>{event.summary}</span><small>{formatDate(event.created_at)}</small></li>)}
            </ol>
          </section>
        </aside>
      </div>

      <div className="ws-export">
        <button type="button" className="btn btn-outline" onClick={() => window.print()}><Download size={16} aria-hidden="true" />Download summary (PDF)</button>
        <span className="ws-muted">Opens your print dialog. Choose "Save as PDF". Private notes are never included.</span>
      </div>

      {ws.is_writable && (
        <section className="pg-card ws-close" aria-label="Complete this mentorship">
          <div>
            <h2>Complete this mentorship</h2>
            <p className="ws-muted"><Lock size={14} aria-hidden="true" /> Either of you can mark it as completed. Everything stays visible as a read-only record, future sessions are cancelled, and new messages are turned off.</p>
          </div>
          <button type="button" className="btn btn-outline" onClick={() => setClosing(true)}>Complete mentorship</button>
        </section>
      )}

      {closing && (
        <ConfirmDialog
          title="Complete this mentorship?" confirmLabel="Yes, complete it" busy={busy} onConfirm={close} onClose={() => setClosing(false)} danger
          message="This ends the active mentorship for both of you. It cannot be reopened, but nothing is deleted."
        >
          <div className="register-field">
            <label htmlFor="outcome">Outcome summary (optional)</label>
            <textarea id="outcome" rows={4} maxLength={2000} value={summary} onChange={(event) => setSummary(event.target.value)} placeholder="What did you achieve together?" />
          </div>
        </ConfirmDialog>
      )}
    </div>
  );
}
