import { useCallback, useEffect, useState } from "react";
import { CalendarClock, CalendarDays, CheckCircle2, Clock3 } from "lucide-react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import { DateTile, PageHeader } from "../components/dashboard";
import { apiRequest } from "../services/api";
import { getAuth } from "../services/authStorage";
import { formatEventDate } from "../utils/format";

const timeRange = (slot) => {
  const date = formatEventDate(slot.start_at);
  const end = formatEventDate(slot.end_at);
  const clock = (full) => full.split(", ").pop();
  return { day: date.full.split(", ").slice(0, -1).join(", "), range: `${clock(date.full)} – ${clock(end.full)} EAT` };
};

export default function BookingPage() {
  const user = getAuth()?.user;
  const isMentor = (user?.community_role || user?.role) === "mentor";
  const [requests, setRequests] = useState([]);
  const [selectedRequest, setSelectedRequest] = useState("");
  const [slots, setSlots] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const bookingRows = await apiRequest("/api/bookings/me");
      setBookings(bookingRows);
      if (!isMentor) {
        const outgoing = await apiRequest("/api/mentorships/outgoing");
        const accepted = outgoing.filter((request) => request.status === "accepted");
        setRequests(accepted);
        setSelectedRequest((current) => accepted.some((item) => String(item.id) === current)
          ? current : accepted[0] ? String(accepted[0].id) : "");
      }
    } catch (err) {
      setError(err.message || "Unable to load booking information.");
    } finally { setLoading(false); }
  }, [isMentor]);

  useEffect(() => { queueMicrotask(() => { void loadData(); }); }, [loadData]);

  useEffect(() => {
    if (isMentor || !selectedRequest) { queueMicrotask(() => { setSlots([]); setLoadingSlots(false); }); return; }
    const mentorship = requests.find((request) => String(request.id) === selectedRequest);
    if (!mentorship) { queueMicrotask(() => { setSlots([]); setLoadingSlots(false); }); return; }
    let active = true;
    queueMicrotask(() => { if (active) setLoadingSlots(true); });
    apiRequest(`/api/availability/mentor/${mentorship.mentor_id}`)
      .then((items) => { if (active) setSlots(items); })
      .catch((err) => { if (active) { setSlots([]); setError(err.message || "Unable to load available times."); } })
      .finally(() => { if (active) setLoadingSlots(false); });
    return () => { active = false; };
  }, [isMentor, requests, selectedRequest]);

  async function bookSlot(availabilityId) {
    if (!selectedRequest || saving) return;
    setSaving(true); setError(""); setNotice("");
    try {
      await apiRequest("/api/bookings", { method: "POST", body: JSON.stringify({ mentorship_id: Number(selectedRequest), availability_id: availabilityId }) });
      setNotice("Your mentoring session is confirmed.");
      await loadData();
      const mentorship = requests.find((request) => String(request.id) === selectedRequest);
      if (mentorship) setSlots(await apiRequest(`/api/availability/mentor/${mentorship.mentor_id}`));
    } catch (err) { setError(err.message || "Unable to book this session."); }
    finally { setSaving(false); }
  }

  async function cancelBooking(bookingId) {
    setSaving(true); setError(""); setNotice("");
    try {
      await apiRequest(`/api/bookings/${bookingId}/cancel`, { method: "PATCH" });
      setNotice("The session was cancelled.");
      await loadData();
      if (!isMentor && selectedRequest) {
        const mentorship = requests.find((request) => String(request.id) === selectedRequest);
        if (mentorship) setSlots(await apiRequest(`/api/availability/mentor/${mentorship.mentor_id}`));
      }
    } catch (err) { setError(err.message || "Unable to cancel this session."); }
    finally { setSaving(false); }
  }

  const upcoming = bookings.filter((booking) => booking.status === "confirmed" && booking.start_at && new Date(booking.start_at) >= new Date());
  const earlier = bookings.filter((booking) => !upcoming.includes(booking));

  const sessionCard = (booking) => {
    const when = booking.start_at ? timeRange({ start_at: booking.start_at, end_at: booking.end_at }) : null;
    return (
      <article className={`pg-card pg-session ${booking.status === "cancelled" ? "is-cancelled" : ""}`} key={booking.id}>
        {booking.start_at ? <DateTile iso={booking.start_at} /> : <div className="pg-date" aria-hidden="true"><CalendarClock size={20} /></div>}
        <div>
          <strong>{when ? when.day : "Session"}</strong>
          <span>{when ? when.range : ""}</span>
          <span>With {isMentor ? booking.mentee_name || "your mentee" : booking.mentor_name || "your mentor"}</span>
        </div>
        <div className="pg-actions">
          <span className={`pg-chip is-${booking.status}`}>{booking.status}</span>
          {booking.status === "confirmed" && <button type="button" className="btn btn-outline" disabled={saving} onClick={() => cancelBooking(booking.id)}>Cancel</button>}
        </div>
      </article>
    );
  };

  return <div className="app"><Navbar />
    <main className="pg-page">
      <PageHeader
        eyebrow="MENTORSHIP SCHEDULING"
        title={isMentor ? "My sessions" : "Book a session"}
        subtitle={isMentor ? "See the sessions your mentees have booked and manage changes." : "Choose an accepted mentorship, then pick a time that works for you."}
        actions={isMentor
          ? <Link to="/availability" className="btn btn-primary"><CalendarDays size={17} aria-hidden="true" />Manage availability</Link>
          : <Link to="/my-mentorships" className="btn btn-outline">My mentorships</Link>}
      />
      {error && <div className="page-alert" role="alert">{error}</div>}
      {notice && <div className="pg-success" role="status" style={{ marginBottom: 16 }}><CheckCircle2 size={18} aria-hidden="true" />{notice}</div>}

      {loading ? <div className="pg-card pg-skeleton" role="status" aria-label="Loading your schedule" /> : (
        <div className="pg-layout">
          <div className="pg-main">
            {!isMentor && (
              <section className="pg-card pg-picker" aria-labelledby="bk-pick">
                <h2 id="bk-pick">Choose a mentor</h2>
                {requests.length === 0 ? (
                  <div className="pg-empty" style={{ padding: "12px 0" }}>
                    <p>You can book once a mentor accepts your request.</p>
                    <Link to="/mentors" className="btn btn-primary">Find a mentor</Link>
                  </div>
                ) : (
                  <>
                    <label htmlFor="bk-select">Accepted mentorship</label>
                    <select id="bk-select" value={selectedRequest} onChange={(event) => setSelectedRequest(event.target.value)}>
                      {requests.map((request) => <option key={request.id} value={request.id}>{request.mentor_name || "Mentor"}</option>)}
                    </select>
                  </>
                )}
              </section>
            )}

            {!isMentor && requests.length > 0 && (
              <section aria-labelledby="bk-open" className="pg-main">
                <div className="pg-section-title"><h2 id="bk-open">Available sessions</h2><span>{slots.length} open</span></div>
                {loadingSlots ? <div className="pg-card pg-skeleton" role="status" aria-label="Loading available times" /> : slots.length === 0 ? (
                  <div className="pg-card pg-empty"><Clock3 size={26} aria-hidden="true" /><h3>No open times yet</h3><p>Your mentor has not published availability. Check back soon, or send them a message.</p><Link to="/chats" className="btn btn-outline">Message your mentor</Link></div>
                ) : slots.map((slot) => {
                  const when = timeRange(slot);
                  return (
                    <article className="pg-card pg-session" key={slot.id}>
                      <DateTile iso={slot.start_at} />
                      <div><strong>{when.day}</strong><span><Clock3 size={13} aria-hidden="true" /> {when.range}</span></div>
                      <button type="button" className="btn btn-primary" disabled={saving} onClick={() => bookSlot(slot.id)}>{saving ? "Booking…" : "Book this time"}</button>
                    </article>
                  );
                })}
              </section>
            )}

            {isMentor && (
              <section aria-labelledby="bk-up" className="pg-main">
                <div className="pg-section-title"><h2 id="bk-up">Upcoming sessions</h2><span>{upcoming.length} booked</span></div>
                {upcoming.length === 0
                  ? <div className="pg-card pg-empty"><CalendarClock size={26} aria-hidden="true" /><h3>No sessions booked yet</h3><p>Publish availability so your mentees can book time with you.</p><Link to="/availability" className="btn btn-primary">Add availability</Link></div>
                  : upcoming.map(sessionCard)}
              </section>
            )}
          </div>

          <aside className="pg-aside" aria-label="Your schedule">
            {!isMentor && (
              <section className="pg-main">
                <div className="pg-section-title"><h2>Your sessions</h2><span>{upcoming.length} upcoming</span></div>
                {upcoming.length === 0 ? <div className="pg-card"><p className="pg-note">No upcoming sessions. Book a time to get started.</p></div> : upcoming.map(sessionCard)}
              </section>
            )}
            {earlier.length > 0 && (
              <section className="pg-main">
                <div className="pg-section-title"><h2>Past and cancelled</h2></div>
                {earlier.map(sessionCard)}
              </section>
            )}
            {isMentor && earlier.length === 0 && <div className="pg-card"><p className="pg-note">Past and cancelled sessions will appear here.</p></div>}
          </aside>
        </div>
      )}
    </main>
  </div>;
}
