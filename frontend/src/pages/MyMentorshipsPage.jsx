import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { CalendarClock, Check, Clock, Compass, MessageCircle, Send, X } from "lucide-react";
import Navbar from "../components/Navbar";
import { DateTile, FilterTabs, PageHeader, StatCard } from "../components/dashboard";
import { apiRequest } from "../services/api";
import { formatDay, formatEventDate, initials, timeAgo } from "../utils/format";

const tabs = ["all", "pending", "accepted", "declined"];

export default function MyMentorshipsPage() {
  const [requests, setRequests] = useState([]);
  const [nextSession, setNextSession] = useState(null);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([
      apiRequest("/api/mentorships/outgoing"),
      apiRequest("/api/bookings/me").catch(() => []),
    ]).then(([outgoing, bookings]) => {
      if (!active) return;
      setRequests(outgoing);
      const upcoming = bookings
        .filter((booking) => booking.status === "confirmed" && booking.start_at && new Date(booking.start_at) >= new Date())
        .sort((a, b) => new Date(a.start_at) - new Date(b.start_at));
      setNextSession(upcoming[0] || null);
    }).catch((err) => {
      if (active) setError(err.message || "Unable to load your mentorship requests.");
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const counts = useMemo(() => ({
    all: requests.length,
    pending: requests.filter((item) => item.status === "pending").length,
    accepted: requests.filter((item) => item.status === "accepted").length,
    declined: requests.filter((item) => item.status === "declined").length,
  }), [requests]);
  const visible = requests.filter((item) => filter === "all" || item.status === filter);

  return (
    <div className="app">
      <Navbar />
      <main className="pg-page">
        <PageHeader
          eyebrow="YOUR MENTORSHIP JOURNEY"
          title="My mentorships"
          subtitle="Track your requests, replies and upcoming sessions."
          actions={<Link to="/mentors" className="btn btn-primary"><Compass size={17} aria-hidden="true" />Find a mentor</Link>}
        />

        {error && <div className="page-alert" role="alert">{error}</div>}

        {!loading && !error && requests.length > 0 && (
          <section className="pg-stats" aria-label="Summary">
            <StatCard icon={Clock} label="Awaiting response" value={counts.pending} />
            <StatCard icon={Check} label="Active mentorships" value={counts.accepted} tone="accent" />
            <StatCard icon={X} label="Declined" value={counts.declined} />
            <StatCard icon={Send} label="Requests sent" value={counts.all} />
          </section>
        )}

        {nextSession && (
          <section className="pg-card pg-session" aria-label="Next session" style={{ marginBottom: 24 }}>
            <DateTile iso={nextSession.start_at} />
            <div>
              <span className="eyebrow">NEXT SESSION</span>
              <strong>{formatEventDate(nextSession.start_at).full} EAT</strong>
              <span>With {nextSession.mentor_name || "your mentor"}</span>
            </div>
            <Link to="/booking" className="btn btn-outline"><CalendarClock size={16} aria-hidden="true" />View sessions</Link>
          </section>
        )}

        {loading && <div className="pg-main">{[1, 2].map((item) => <div className="pg-card pg-skeleton" key={item} role="status" aria-label="Loading your requests" />)}</div>}

        {!loading && !error && requests.length === 0 && (
          <section className="pg-card pg-empty">
            <Compass size={30} aria-hidden="true" />
            <h2>Your mentorship journey starts here</h2>
            <p>Explore alumni mentors, find someone who fits your goals, and send a thoughtful request.</p>
            <Link to="/mentors" className="btn btn-primary">Discover mentors</Link>
          </section>
        )}

        {!loading && !error && requests.length > 0 && (
          <div className="pg-main">
            <FilterTabs
              label="Filter requests"
              value={filter}
              onChange={setFilter}
              options={tabs.map((id) => ({ id, label: id[0].toUpperCase() + id.slice(1), count: counts[id] }))}
            />
            {visible.length === 0 && <section className="pg-card pg-empty"><h3>No {filter} requests</h3><p>Try another filter.</p></section>}
            {visible.map((request) => (
              <article className="pg-card pg-row-card" key={request.id}>
                <div className="pg-row-top">
                  <span className="pg-avatar" aria-hidden="true">{initials(request.mentor_name)}</span>
                  <div>
                    <h3>{request.mentor_name || "Mentor"}</h3>
                    <small>Sent {timeAgo(request.created_at)}{request.responded_at ? ` · replied ${formatDay(request.responded_at)}` : ""}</small>
                  </div>
                  <span className={`pg-chip is-${request.status}`}>{request.status}</span>
                </div>
                <blockquote className="pg-quote">
                  <span>Your message</span>
                  <p>{request.motivation || "No message was included with this request."}</p>
                </blockquote>
                {request.status === "accepted" && (
                  <div className="pg-actions">
                    <Link to="/booking" className="btn btn-primary"><CalendarClock size={16} aria-hidden="true" />Book a session</Link>
                    <Link to="/chats" className="btn btn-outline"><MessageCircle size={16} aria-hidden="true" />Message</Link>
                  </div>
                )}
                {request.status === "pending" && <p className="pg-note"><Clock size={15} aria-hidden="true" />Waiting for {request.mentor_name?.split(" ")[0] || "the mentor"} to respond. You will be notified.</p>}
                {request.status === "declined" && (
                  <div className="pg-actions">
                    <Link to="/mentors" className="btn btn-outline"><Compass size={16} aria-hidden="true" />Find another mentor</Link>
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
