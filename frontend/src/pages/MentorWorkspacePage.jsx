import { useCallback, useEffect, useMemo, useState } from "react";
import { CalendarClock, CalendarDays, Check, Clock3, Inbox, RefreshCw, Search, Users, X } from "lucide-react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import { DateTile, FilterTabs, PageHeader, StatCard } from "../components/dashboard";
import { apiRequest } from "../services/api";
import { getAuth } from "../services/authStorage";
import { formatDay, formatEventDate, initials } from "../utils/format";
import WorkspaceGlance from "../components/WorkspaceGlance";

const filters = ["pending", "accepted", "completed", "declined", "all"];

export default function MentorWorkspacePage() {
  const firstName = getAuth()?.user?.full_name?.split(" ")[0] || "";
  const [requests, setRequests] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [openSlots, setOpenSlots] = useState(0);
  const [summary, setSummary] = useState({});
  const [chosenFilter, setFilter] = useState(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [processing, setProcessing] = useState(null);

  const loadAll = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const [incoming, bookings, availability, progress] = await Promise.all([
        apiRequest("/api/mentorships/incoming"),
        apiRequest("/api/bookings/me").catch(() => []),
        apiRequest("/api/availability/me").catch(() => []),
        apiRequest("/api/mentorships/summary").catch(() => ({})),
      ]);
      setRequests(incoming);
      setSummary(progress);
      setSessions(bookings
        .filter((booking) => booking.status === "confirmed" && booking.start_at && new Date(booking.start_at) >= new Date())
        .sort((a, b) => new Date(a.start_at) - new Date(b.start_at)));
      setOpenSlots(availability.filter((slot) => slot.status === "available" && new Date(slot.start_at) > new Date()).length);
    } catch (err) { setError(err.message || "Could not load your dashboard."); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { queueMicrotask(() => { void loadAll(); }); }, [loadAll]);

  const counts = useMemo(() => ({
    all: requests.length,
    pending: requests.filter((item) => item.status === "pending").length,
    accepted: requests.filter((item) => item.status === "accepted").length,
    completed: requests.filter((item) => item.status === "completed").length,
    declined: requests.filter((item) => item.status === "declined").length,
  }), [requests]);

  // Open on the requests that need an answer, or on everything when none are waiting.
  const filter = chosenFilter ?? (counts.pending ? "pending" : "all");

  const visible = useMemo(() => requests.filter((request) => {
    const term = search.trim().toLowerCase();
    return (filter === "all" || request.status === filter) &&
      (!term || (request.mentee_name || "").toLowerCase().includes(term) || (request.motivation || "").toLowerCase().includes(term));
  }), [requests, filter, search]);

  async function respond(id, decision) {
    setProcessing(id); setError(""); setNotice("");
    try {
      const updated = await apiRequest(`/api/mentorships/${id}/respond`, { method: "PATCH", body: JSON.stringify({ decision }) });
      setRequests((current) => current.map((item) => item.id === id ? updated : item));
      setNotice(decision === "accepted" ? `You accepted ${updated.mentee_name}'s request.` : `You declined ${updated.mentee_name}'s request.`);
    } catch (err) { setError(err.message || "Could not update the request."); }
    finally { setProcessing(null); }
  }

  return <div className="app"><Navbar /><main className="pg-page">
    <PageHeader
      eyebrow="MENTOR DASHBOARD"
      title={firstName ? `Welcome back, ${firstName}` : "Your mentor dashboard"}
      subtitle="Respond to mentees, keep your calendar open and prepare for upcoming sessions."
      actions={<><Link className="btn btn-primary" to="/availability"><CalendarDays size={17} aria-hidden="true" />Manage availability</Link><Link className="btn btn-outline" to="/chats">Messages</Link></>}
    />

    <section className="pg-stats" aria-label="Summary">
      <StatCard icon={Inbox} label="Awaiting your response" value={counts.pending} tone={counts.pending ? "accent" : undefined} />
      <StatCard icon={Users} label="Active mentees" value={counts.accepted} />
      <StatCard icon={CalendarClock} label="Upcoming sessions" value={sessions.length} />
      <StatCard icon={Clock3} label="Open time slots" value={openSlots} hint={openSlots ? undefined : "Add availability so mentees can book"} />
    </section>

    {error && <div className="page-alert" role="alert">{error}</div>}
    {notice && <div className="pg-success" role="status" style={{ marginBottom: 16 }}><Check size={17} aria-hidden="true" />{notice}</div>}

    <div className="pg-layout">
      <section className="pg-main" aria-labelledby="mw-requests">
        <div className="pg-section-title">
          <h2 id="mw-requests">Mentorship requests</h2>
          <button className="btn btn-outline" type="button" onClick={loadAll} disabled={loading}><RefreshCw size={15} aria-hidden="true" />Refresh</button>
        </div>
        <div className="pg-toolbar">
          <FilterTabs label="Filter requests" value={filter} onChange={setFilter} options={filters.map((id) => ({ id, label: id[0].toUpperCase() + id.slice(1), count: counts[id] }))} />
          <label className="pg-search"><Search size={17} aria-hidden="true" /><span className="visually-hidden">Search requests</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by name or message" /></label>
        </div>

        {loading ? <div className="pg-card pg-skeleton" role="status" aria-label="Loading requests" /> : visible.length === 0 ? (
          <div className="pg-card pg-empty">
            <Inbox size={28} aria-hidden="true" />
            <h3>{requests.length ? `No ${filter === "all" ? "" : filter + " "}requests` : "Your inbox is clear"}</h3>
            <p>{requests.length ? "Try another filter or search term." : "New mentorship requests will appear here."}</p>
            {requests.length > 0 && <button className="btn btn-outline" onClick={() => { setFilter("all"); setSearch(""); }}>Show all requests</button>}
          </div>
        ) : visible.map((request) => (
          <article className="pg-card pg-row-card" key={request.id}>
            <div className="pg-row-top">
              <span className="pg-avatar" aria-hidden="true">{initials(request.mentee_name)}</span>
              <div>
                <h3>{request.mentee_name || "Mentee"}</h3>
                <small>Requested {request.created_at ? formatDay(request.created_at) : "recently"}</small>
              </div>
              <span className={`pg-chip is-${request.status}`}>{request.status}</span>
            </div>
            <blockquote className="pg-quote">
              <span>Why they want your mentorship</span>
              <p>{request.motivation || "No introduction was included with this request."}</p>
            </blockquote>
            {request.status === "pending" && (
              <div className="pg-actions">
                <button className="btn btn-primary" type="button" disabled={processing === request.id} onClick={() => respond(request.id, "accepted")}><Check size={16} aria-hidden="true" />{processing === request.id ? "Saving…" : "Accept"}</button>
                <button className="btn btn-outline" type="button" disabled={processing === request.id} onClick={() => respond(request.id, "declined")}><X size={16} aria-hidden="true" />Decline</button>
              </div>
            )}
            {summary[request.id] && <WorkspaceGlance info={summary[request.id]} />}
            {(request.status === "accepted" || request.status === "completed") && (
              <div className="pg-actions">
                <Link to={`/mentorships/${request.id}`} className="btn btn-primary">Open workspace</Link>
                <Link to="/chats" className="btn btn-outline">{request.status === "completed" ? "View messages" : `Message ${request.mentee_name?.split(" ")[0]}`}</Link>
                <Link to="/booking" className="btn btn-outline">View sessions</Link>
              </div>
            )}
          </article>
        ))}
      </section>

      <aside className="pg-aside" aria-label="Upcoming sessions">
        <section className="pg-main">
          <div className="pg-section-title"><h2>Next sessions</h2><Link to="/booking" className="cm-link">View all</Link></div>
          {loading ? <div className="pg-card pg-skeleton" role="status" /> : sessions.length === 0 ? (
            <div className="pg-card pg-empty" style={{ padding: "24px 16px" }}>
              <CalendarClock size={24} aria-hidden="true" />
              <p>No sessions booked yet.</p>
              <Link to="/availability" className="btn btn-outline">Add availability</Link>
            </div>
          ) : sessions.slice(0, 4).map((session) => (
            <article className="pg-card pg-session" key={session.id}>
              <DateTile iso={session.start_at} />
              <div><strong>{session.mentee_name || "Your mentee"}</strong><span>{formatEventDate(session.start_at).full} EAT</span></div>
            </article>
          ))}
        </section>
      </aside>
    </div>
  </main></div>;
}
