import { useEffect, useState } from "react";
import { Briefcase, CalendarDays, ExternalLink, Mail, MapPin, Users } from "lucide-react";
import { apiRequest } from "../../services/api";
import { formatDay, formatEventDate } from "../../utils/format";

function useList(path) {
  const [state, setState] = useState({ items: [], loading: true, error: "" });
  useEffect(() => {
    let active = true;
    apiRequest(path)
      .then((items) => { if (active) setState({ items, loading: false, error: "" }); })
      .catch((error) => { if (active) setState({ items: [], loading: false, error: error.message || "Unable to load." }); });
    return () => { active = false; };
  }, [path]);
  return [state, (items) => setState((current) => ({ ...current, items }))];
}

export function EventsCard() {
  const [{ items, loading, error }, setItems] = useList("/api/community/events");
  const [busyId, setBusyId] = useState(null);
  const [actionError, setActionError] = useState("");

  async function toggle(event) {
    setBusyId(event.id);
    setActionError("");
    try {
      const result = await apiRequest(`/api/community/events/${event.id}/rsvp`, { method: event.going_by_me ? "DELETE" : "PUT" });
      setItems(items.map((item) => (item.id === event.id ? { ...item, ...result } : item)));
    } catch (requestError) { setActionError(requestError.message || "Unable to update your RSVP."); }
    finally { setBusyId(null); }
  }

  return (
    <section className="cm-card cm-side" aria-labelledby="cm-events-title">
      <h2 id="cm-events-title"><CalendarDays size={18} aria-hidden="true" />Upcoming events</h2>
      {loading ? <p className="cm-muted">Loading…</p> : error ? <p className="cm-muted" role="alert">{error}</p> : items.length === 0 ? (
        <p className="cm-muted">No upcoming events yet. New events appear here as they are announced.</p>
      ) : (
        <ul className="cm-list">
          {items.map((event) => {
            const date = formatEventDate(event.starts_at);
            return (
              <li key={event.id} className="cm-event">
                <div className="cm-date" aria-hidden="true"><span>{date.month}</span><strong>{date.day}</strong></div>
                <div>
                  <h3>{event.title}</h3>
                  <p className="cm-meta">{date.full} EAT</p>
                  <p className="cm-meta"><MapPin size={13} aria-hidden="true" />{event.location}</p>
                  <p className="cm-meta"><Users size={13} aria-hidden="true" />{event.going_count} going</p>
                  <div className="cm-actions">
                    <button
                      type="button"
                      className={`btn ${event.going_by_me ? "btn-outline" : "btn-primary"} cm-small`}
                      aria-pressed={event.going_by_me}
                      disabled={busyId === event.id}
                      onClick={() => toggle(event)}
                    >
                      {event.going_by_me ? "Going · Cancel RSVP" : "I'm going"}
                    </button>
                    {event.link && <a className="cm-link" href={event.link} target="_blank" rel="noopener noreferrer">Details <ExternalLink size={13} aria-hidden="true" /></a>}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
      {actionError && <p className="form-error" role="alert">{actionError}</p>}
    </section>
  );
}

export function JobsCard() {
  const [{ items, loading, error }] = useList("/api/community/jobs");

  return (
    <section className="cm-card cm-side" aria-labelledby="cm-jobs-title">
      <h2 id="cm-jobs-title"><Briefcase size={18} aria-hidden="true" />Job opportunities</h2>
      {loading ? <p className="cm-muted">Loading…</p> : error ? <p className="cm-muted" role="alert">{error}</p> : items.length === 0 ? (
        <p className="cm-muted">No open roles right now. Openings shared by Kenya Airways appear here.</p>
      ) : (
        <ul className="cm-list">
          {items.map((job) => (
            <li key={job.id} className="cm-job">
              <h3>{job.title}</h3>
              <p className="cm-meta">{job.company} · {job.employment_type}</p>
              <p className="cm-meta"><MapPin size={13} aria-hidden="true" />{job.location}</p>
              {job.closes_at && <p className="cm-meta">Closes {formatDay(job.closes_at)}</p>}
              <p className="cm-job-text">{job.description}</p>
              {job.apply_url
                ? <a className="btn btn-outline cm-small" href={job.apply_url} target="_blank" rel="noopener noreferrer">Apply <ExternalLink size={13} aria-hidden="true" /></a>
                : <a className="btn btn-outline cm-small" href={`mailto:${job.contact_email}`}><Mail size={13} aria-hidden="true" />Contact {job.contact_email}</a>}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
