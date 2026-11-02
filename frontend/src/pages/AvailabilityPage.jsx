import { useCallback, useEffect, useMemo, useState } from "react";
import { CalendarDays, ChevronLeft, ChevronRight, Plus } from "lucide-react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import Navbar from "../components/Navbar";
import { apiRequest } from "../services/api";

const EMPTY_FORM = { start_at: "", end_at: "" };
const weekdayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const toLocalDateKey = (value) => {
  const date = new Date(value);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

function formatTime(value) {
  return new Date(value).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

export default function AvailabilityPage() {
  const [form, setForm] = useState(EMPTY_FORM);
  const [slots, setSlots] = useState([]);
  const [month, setMonth] = useState(() => new Date(new Date().getFullYear(), new Date().getMonth(), 1));
  const [selectedDay, setSelectedDay] = useState(() => toLocalDateKey(new Date()));
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [minimumStart] = useState(() => new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16));

  const loadSlots = useCallback(async () => {
    setLoading(true); setError("");
    try { setSlots(await apiRequest("/api/availability/me")); }
    catch (err) { setError(err.message || "Unable to load your calendar."); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { queueMicrotask(() => { void loadSlots(); }); }, [loadSlots]);

  const slotsByDay = useMemo(() => slots.reduce((map, slot) => {
    const key = toLocalDateKey(slot.start_at);
    map.set(key, [...(map.get(key) || []), slot]);
    return map;
  }, new Map()), [slots]);

  const calendarCells = useMemo(() => {
    const year = month.getFullYear(); const monthIndex = month.getMonth();
    const firstDay = new Date(year, monthIndex, 1);
    const mondayOffset = (firstDay.getDay() + 6) % 7;
    const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
    return [...Array(mondayOffset).fill(null), ...Array.from({ length: daysInMonth }, (_, i) => new Date(year, monthIndex, i + 1))];
  }, [month]);

  const selectedSlots = (slotsByDay.get(selectedDay) || []).slice().sort((a, b) => new Date(a.start_at) - new Date(b.start_at));
  const bookedCount = slots.filter((slot) => slot.status === "booked").length;
  const availableCount = slots.filter((slot) => slot.status === "available" && new Date(slot.start_at) > new Date()).length;

  async function publish(event) {
    event.preventDefault(); setSaving(true); setError(""); setNotice("");
    try {
      const start = new Date(form.start_at); const end = new Date(form.end_at);
      if (Number.isNaN(start.valueOf()) || Number.isNaN(end.valueOf()) || end <= start) throw new Error("Choose an end time that is after the start time.");
      const slot = await apiRequest("/api/availability", { method: "POST", body: JSON.stringify({ start_at: start.toISOString(), end_at: end.toISOString() }) });
      setNotice("Availability added to your calendar.");
      setSelectedDay(toLocalDateKey(slot.start_at));
      setMonth(new Date(new Date(slot.start_at).getFullYear(), new Date(slot.start_at).getMonth(), 1));
      setForm(EMPTY_FORM);
      await loadSlots();
    } catch (err) { setError(err.message || "Unable to publish availability."); }
    finally { setSaving(false); }
  }

  return <div className="app"><Navbar /><main className="availability-page-shell">
    <Link className="workflow-back-link" to="/mentor-workspace"><ArrowLeft size={16} />Back to workspace</Link><header className="availability-heading"><div className="availability-heading-icon"><CalendarDays size={23} /></div><div><span className="eyebrow">YOUR MENTOR CALENDAR</span><h1>My Availability</h1><p>Publish times for mentees and keep track of sessions already booked.</p></div></header>
    {error && <div className="page-alert" role="alert">{error}</div>}
    {notice && <div className="booking-success" role="status">{notice}</div>}
    <div className="availability-overview"><div><span>Available times</span><strong>{availableCount}</strong></div><div><span>Booked sessions</span><strong>{bookedCount}</strong></div><div><span>Total calendar slots</span><strong>{slots.length}</strong></div></div>
    <div className="availability-layout">
      <section className="availability-calendar-panel">
        <div className="calendar-toolbar"><div><span className="eyebrow">SCHEDULE</span><h2>{month.toLocaleDateString(undefined, { month: "long", year: "numeric" })}</h2></div><div className="calendar-month-controls"><button type="button" aria-label="Previous month" onClick={() => setMonth((value) => new Date(value.getFullYear(), value.getMonth() - 1, 1))}><ChevronLeft /></button><button type="button" aria-label="Next month" onClick={() => setMonth((value) => new Date(value.getFullYear(), value.getMonth() + 1, 1))}><ChevronRight /></button></div></div>
        <div className="availability-calendar-grid" role="grid" aria-label="Mentor availability calendar">{weekdayNames.map((day) => <div className="calendar-weekday" key={day}>{day}</div>)}{calendarCells.map((date, index) => {
          if (!date) return <div className="calendar-day is-blank" key={`blank-${index}`} aria-hidden="true" />;
          const key = toLocalDateKey(date); const daySlots = slotsByDay.get(key) || []; const hasAvailable = daySlots.some((slot) => slot.status === "available"); const hasBooked = daySlots.some((slot) => slot.status === "booked");
          return <button type="button" role="gridcell" aria-label={`${date.toLocaleDateString()}${daySlots.length ? `, ${daySlots.length} scheduled slot${daySlots.length > 1 ? "s" : ""}` : ""}`} aria-pressed={selectedDay === key} onClick={() => setSelectedDay(key)} className={`calendar-day ${selectedDay === key ? "is-selected" : ""} ${toLocalDateKey(new Date()) === key ? "is-today" : ""}`} key={key}><span>{date.getDate()}</span><span className="calendar-day-markers">{hasAvailable && <i className="available-marker" title="Available" />}{hasBooked && <i className="booked-marker" title="Booked" />}</span></button>;
        })}</div>
        <div className="calendar-legend"><span><i className="available-marker" /> Available</span><span><i className="booked-marker" /> Booked</span></div>
      </section>

      <section className="availability-day-panel"><div className="availability-day-heading"><div><span className="eyebrow">SELECTED DATE</span><h2>{new Date(`${selectedDay}T12:00:00`).toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" })}</h2></div><span className="day-slot-count">{selectedSlots.length}</span></div>
        {loading ? <p className="availability-empty">Loading your schedule…</p> : selectedSlots.length === 0 ? <div className="availability-empty"><CalendarDays size={26} /><p>No sessions scheduled for this day.</p><span>Add an available time below.</span></div> : <div className="availability-slot-list">{selectedSlots.map((slot) => <article className={`availability-slot-item is-${slot.status}`} key={slot.id}><span className="availability-slot-indicator" /><div><strong>{formatTime(slot.start_at)} – {formatTime(slot.end_at)}</strong><small>{slot.status === "booked" ? "Booked session" : "Available to book"}</small></div>{slot.status === "booked" && <Link to="/booking">Manage</Link>}</article>)}</div>}
      </section>
    </div>

    <section className="availability-form-panel"><div className="availability-form-intro"><span className="availability-form-icon"><Plus size={19} /></span><div><h2>Add availability</h2><p>Choose a future time window. Your local timezone is used.</p></div></div><form onSubmit={publish} className="availability-form-grid"><label>Start date and time<input type="datetime-local" value={form.start_at} min={minimumStart} onChange={(event) => setForm((current) => ({ ...current, start_at: event.target.value, end_at: current.end_at && current.end_at <= event.target.value ? "" : current.end_at }))} required /></label><label>End date and time<input type="datetime-local" value={form.end_at} min={form.start_at || undefined} onChange={(event) => setForm((current) => ({ ...current, end_at: event.target.value }))} required /></label><button className="btn btn-primary" type="submit" disabled={saving}>{saving ? "Adding time…" : "Add to calendar"}</button></form></section>
  </main></div>;
}
