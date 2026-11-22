import { useCallback, useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { AlertCircle } from "lucide-react";
import { apiRequest } from "../../services/api";
import { Empty, Loading, StatusChip } from "./ui";
import { formatDate, formatWhen, label } from "./format";

function Meter({ title, done, total, percent, unit }) {
  return (
    <article className="pg-card ws-meter">
      <h3>{title}</h3>
      {percent === null
        ? <p className="ws-muted">Nothing recorded yet, so there is no percentage to show.</p>
        : <>
          <strong>{done} of {total} {unit}</strong>
          <div className="ws-bar" role="progressbar" aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100} aria-label={`${title}: ${percent}%`}><span style={{ width: `${percent}%` }} /></div>
          <small>{percent}% complete</small>
        </>}
    </article>
  );
}

export default function ProgressTab() {
  const { base } = useOutletContext();
  const [progress, setProgress] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [error, setError] = useState("");
  const [showAll, setShowAll] = useState(false);

  const load = useCallback(async () => {
    try {
      const [p, t] = await Promise.all([apiRequest(`${base}/progress`), apiRequest(`${base}/timeline`)]);
      setProgress(p); setTimeline(t); setError("");
    } catch (err) { setError(err.message || "Unable to load progress."); }
  }, [base]);
  useEffect(() => { queueMicrotask(() => { void load(); }); }, [load]);

  if (error) return <div className="page-alert" role="alert">{error}</div>;
  if (!progress || !timeline) return <Loading text="Loading progress" />;
  const { goals, action_items: items, sessions } = progress;

  return (
    <div className="ws-stack">
      <div className="pg-section-title"><h2>Progress</h2></div>
      <div className="ws-grid-2">
        <Meter title="Goals" done={goals.completed} total={goals.total - goals.on_hold} percent={goals.percent_complete} unit="goals" />
        <Meter title="Action items" done={items.completed} total={items.total} percent={items.percent_complete} unit="items" />
      </div>
      <p className="ws-muted ws-method"><strong>How this is calculated.</strong> {progress.method}</p>

      <section className="pg-stats" aria-label="Session counts">
        <article className="pg-card pg-stat"><div><strong>{sessions.completed}</strong><span>Sessions completed</span></div></article>
        <article className="pg-card pg-stat"><div><strong>{sessions.upcoming}</strong><span>Upcoming</span></div></article>
        <article className="pg-card pg-stat"><div><strong>{sessions.cancelled}</strong><span>Cancelled</span></div></article>
        <article className="pg-card pg-stat"><div><strong>{goals.on_hold}</strong><span>Goals on hold</span></div></article>
      </section>

      <section className="ws-block" aria-labelledby="attn">
        <h3 id="attn">What needs attention</h3>
        {progress.needs_attention.length === 0
          ? <p className="ws-muted">Nothing is overdue or waiting to be updated.</p>
          : <ul className="pg-card ws-plain-list">{progress.needs_attention.map((item) => <li key={`${item.type}-${item.entity_id}`} className="ws-alert-item"><AlertCircle size={15} aria-hidden="true" /><span>{item.message}</span></li>)}</ul>}
      </section>

      <div className="ws-grid-2">
        <section className="ws-block" aria-labelledby="g-status">
          <h3 id="g-status">Goals</h3>
          {progress.goal_list.length === 0 ? <p className="ws-muted">No goals recorded.</p> : progress.goal_list.map((goal) => (
            <article className="pg-card ws-row" key={goal.id}><div><strong>{goal.title}</strong><small>{goal.completed_at ? `Completed ${formatDate(goal.completed_at)}` : goal.target_date ? `Target ${formatDate(goal.target_date)}` : "No target date"}</small></div><StatusChip value={goal.status} /></article>
          ))}
        </section>
        <section className="ws-block" aria-labelledby="done-items">
          <h3 id="done-items">Completed action items</h3>
          {progress.completed_action_items.length === 0 ? <p className="ws-muted">None completed yet.</p> : (
            <ul className="pg-card ws-plain-list">{progress.completed_action_items.map((item) => <li key={item.id}><span>{item.description}</span><small>{item.assigned_to_name} · {formatDate(item.completed_at)}</small></li>)}</ul>
          )}
        </section>
      </div>

      <section className="ws-block" aria-labelledby="done-sessions">
        <h3 id="done-sessions">Completed sessions</h3>
        {progress.completed_sessions.length === 0 ? <p className="ws-muted">No sessions have been marked completed.</p> : (
          <ul className="pg-card ws-plain-list">{progress.completed_sessions.map((session) => <li key={session.id}><span>{session.title}</span><small>{formatWhen(session.scheduled_at)}</small></li>)}</ul>
        )}
      </section>

      <section className="ws-block" aria-labelledby="timeline">
        <h3 id="timeline">Activity timeline</h3>
        <p className="ws-muted">Only things that actually happened, newest first. Private notes never appear here.</p>
        {timeline.length === 0 ? <Empty title="No activity yet" /> : (
          <ol className="ws-timeline">
            {(showAll ? timeline : timeline.slice(0, 8)).map((event) => (
              <li key={`${event.event_type}-${event.id ?? event.created_at}`}>
                <span className={`ws-dot is-${event.event_type}`} aria-hidden="true" />
                <div><strong>{event.summary}</strong><small>{event.actor_name ? `${event.actor_name} · ` : ""}{formatDate(event.created_at)}{event.old_value ? ` · ${label(event.old_value)} → ${label(event.new_value)}` : ""}</small></div>
              </li>
            ))}
          </ol>
        )}
        {timeline.length > 8 && <button type="button" className="btn btn-outline ws-small ws-more" onClick={() => setShowAll(!showAll)}>{showAll ? "Show fewer" : `Show all ${timeline.length} events`}</button>}
      </section>
    </div>
  );
}
