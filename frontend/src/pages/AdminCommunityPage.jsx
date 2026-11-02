import { useCallback, useEffect, useState } from "react";
import { CalendarDays, Briefcase } from "lucide-react";
import Navbar from "../components/Navbar";
import { apiRequest } from "../services/api";
import { formatDay, formatEventDate } from "../utils/format";

const emptyEvent = { title: "", description: "", location: "", starts_at: "", ends_at: "", link: "" };
const emptyJob = { title: "", company: "Kenya Airways", location: "", employment_type: "Full-time", description: "", apply_url: "", contact_email: "", closes_at: "" };
const employmentTypes = ["Full-time", "Part-time", "Contract", "Internship"];

// Admins enter times in East Africa Time (UTC+3), which has no daylight saving.
const eat = (local) => (local ? `${local}:00+03:00` : null);

export default function AdminCommunityPage() {
  const [events, setEvents] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [eventForm, setEventForm] = useState(emptyEvent);
  const [jobForm, setJobForm] = useState(emptyJob);
  const [message, setMessage] = useState({ type: "", text: "" });
  const [busy, setBusy] = useState("");

  const load = useCallback(async () => {
    try {
      const [eventList, jobList] = await Promise.all([
        apiRequest("/api/admin/community/events"),
        apiRequest("/api/admin/community/jobs"),
      ]);
      setEvents(eventList);
      setJobs(jobList);
    } catch (error) { setMessage({ type: "error", text: error.message || "Unable to load events and jobs." }); }
  }, []);

  useEffect(() => { queueMicrotask(() => { void load(); }); }, [load]);

  const field = (setter) => (event) => setter((current) => ({ ...current, [event.target.name]: event.target.value }));

  async function submit(kind, path, body, reset) {
    setBusy(kind);
    setMessage({ type: "", text: "" });
    try {
      await apiRequest(path, { method: "POST", body: JSON.stringify(body) });
      reset();
      setMessage({ type: "success", text: kind === "event" ? "Event published." : "Job published." });
      await load();
    } catch (error) { setMessage({ type: "error", text: error.message || "Unable to save." }); }
    finally { setBusy(""); }
  }

  const createEvent = (event) => {
    event.preventDefault();
    void submit("event", "/api/admin/community/events", {
      title: eventForm.title, description: eventForm.description, location: eventForm.location,
      starts_at: eat(eventForm.starts_at), ends_at: eat(eventForm.ends_at), link: eventForm.link || null,
    }, () => setEventForm(emptyEvent));
  };

  const createJob = (event) => {
    event.preventDefault();
    void submit("job", "/api/admin/community/jobs", {
      title: jobForm.title, company: jobForm.company, location: jobForm.location, employment_type: jobForm.employment_type,
      description: jobForm.description, apply_url: jobForm.apply_url || null, contact_email: jobForm.contact_email || null,
      closes_at: eat(jobForm.closes_at),
    }, () => setJobForm(emptyJob));
  };

  async function act(path) {
    setMessage({ type: "", text: "" });
    try { await apiRequest(path, { method: "PATCH" }); await load(); }
    catch (error) { setMessage({ type: "error", text: error.message || "Unable to update." }); }
  }

  return <div className="app"><Navbar /><main className="admin-community">
    <header>
      <span className="eyebrow">Admin console</span>
      <h1>Events and job opportunities</h1>
      <p>These appear on the community home page for every member. Times are in East Africa Time.</p>
    </header>
    {message.text && <div role={message.type === "error" ? "alert" : "status"} className={message.type === "error" ? "page-alert" : "form-success"}>{message.text}</div>}

    <div className="admin-community-grid">
      <section className="register-section" aria-labelledby="ac-event">
        <header><span><CalendarDays size={16} aria-hidden="true" /></span><div><h2 id="ac-event">New event</h2><p>Members can RSVP from the community page.</p></div></header>
        <form className="register-form" onSubmit={createEvent}>
          <div className="register-field"><label htmlFor="ev-title">Title</label><input id="ev-title" name="title" value={eventForm.title} onChange={field(setEventForm)} minLength={3} maxLength={160} required /></div>
          <div className="register-field"><label htmlFor="ev-desc">Description</label><textarea id="ev-desc" name="description" rows="3" value={eventForm.description} onChange={field(setEventForm)} minLength={10} maxLength={4000} required /></div>
          <div className="register-grid">
            <div className="register-field"><label htmlFor="ev-start">Starts</label><input id="ev-start" type="datetime-local" name="starts_at" value={eventForm.starts_at} onChange={field(setEventForm)} required /></div>
            <div className="register-field"><label htmlFor="ev-end">Ends (optional)</label><input id="ev-end" type="datetime-local" name="ends_at" value={eventForm.ends_at} onChange={field(setEventForm)} /></div>
            <div className="register-field"><label htmlFor="ev-loc">Location</label><input id="ev-loc" name="location" value={eventForm.location} onChange={field(setEventForm)} maxLength={200} required /></div>
            <div className="register-field"><label htmlFor="ev-link">Link (optional)</label><input id="ev-link" type="url" name="link" value={eventForm.link} onChange={field(setEventForm)} placeholder="https://" /></div>
          </div>
          <button className="btn btn-primary" type="submit" disabled={busy === "event"}>{busy === "event" ? "Publishing…" : "Publish event"}</button>
        </form>
      </section>

      <section className="register-section" aria-labelledby="ac-job">
        <header><span><Briefcase size={16} aria-hidden="true" /></span><div><h2 id="ac-job">New job opportunity</h2><p>Add an application link, a contact email, or both.</p></div></header>
        <form className="register-form" onSubmit={createJob}>
          <div className="register-grid">
            <div className="register-field"><label htmlFor="jb-title">Job title</label><input id="jb-title" name="title" value={jobForm.title} onChange={field(setJobForm)} minLength={3} maxLength={160} required /></div>
            <div className="register-field"><label htmlFor="jb-company">Company</label><input id="jb-company" name="company" value={jobForm.company} onChange={field(setJobForm)} maxLength={160} required /></div>
            <div className="register-field"><label htmlFor="jb-loc">Location</label><input id="jb-loc" name="location" value={jobForm.location} onChange={field(setJobForm)} maxLength={200} required /></div>
            <div className="register-field"><label htmlFor="jb-type">Type</label><select id="jb-type" name="employment_type" value={jobForm.employment_type} onChange={field(setJobForm)}>{employmentTypes.map((type) => <option key={type}>{type}</option>)}</select></div>
          </div>
          <div className="register-field"><label htmlFor="jb-desc">Description</label><textarea id="jb-desc" name="description" rows="3" value={jobForm.description} onChange={field(setJobForm)} minLength={10} maxLength={4000} required /></div>
          <div className="register-grid">
            <div className="register-field"><label htmlFor="jb-url">Application link</label><input id="jb-url" type="url" name="apply_url" value={jobForm.apply_url} onChange={field(setJobForm)} placeholder="https://" /></div>
            <div className="register-field"><label htmlFor="jb-mail">Contact email</label><input id="jb-mail" type="email" name="contact_email" value={jobForm.contact_email} onChange={field(setJobForm)} /></div>
            <div className="register-field"><label htmlFor="jb-close">Closes (optional)</label><input id="jb-close" type="datetime-local" name="closes_at" value={jobForm.closes_at} onChange={field(setJobForm)} /></div>
          </div>
          <button className="btn btn-primary" type="submit" disabled={busy === "job"}>{busy === "job" ? "Publishing…" : "Publish job"}</button>
        </form>
      </section>
    </div>

    <div className="admin-community-grid">
      <section className="register-section" aria-labelledby="ac-events-list">
        <h2 id="ac-events-list">All events</h2>
        {events.length === 0 ? <p className="cm-muted">No events yet.</p> : <ul className="admin-community-list">
          {events.map((item) => <li key={item.id}>
            <div><strong>{item.title}</strong><span>{formatEventDate(item.starts_at).full} EAT · {item.location} · {item.going_count} going{item.is_cancelled ? " · Cancelled" : ""}</span></div>
            {!item.is_cancelled && <button type="button" className="btn btn-outline cm-small" onClick={() => act(`/api/admin/community/events/${item.id}/cancel`)}>Cancel event</button>}
          </li>)}
        </ul>}
      </section>
      <section className="register-section" aria-labelledby="ac-jobs-list">
        <h2 id="ac-jobs-list">All jobs</h2>
        {jobs.length === 0 ? <p className="cm-muted">No jobs yet.</p> : <ul className="admin-community-list">
          {jobs.map((item) => <li key={item.id}>
            <div><strong>{item.title}</strong><span>{item.company} · {item.location}{item.closes_at ? ` · closes ${formatDay(item.closes_at)}` : ""}{item.is_active ? "" : " · Closed"}</span></div>
            {item.is_active && <button type="button" className="btn btn-outline cm-small" onClick={() => act(`/api/admin/community/jobs/${item.id}/close`)}>Close job</button>}
          </li>)}
        </ul>}
      </section>
    </div>
  </main></div>;
}
