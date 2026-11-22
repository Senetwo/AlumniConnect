import { useState } from "react";
import { Link } from "react-router-dom";
import { CalendarClock, Check, Clock, MessageCircle, X } from "lucide-react";
import { apiRequest } from "../services/api";

export function RequestStatusChip({ record }) {
  if (!record) return null;
  const copy = {
    pending: { icon: Clock, text: "Request pending" },
    accepted: { icon: Check, text: "Mentor accepted" },
    declined: { icon: X, text: "Request declined" },
  }[record.status];
  if (!copy) return null;
  const Icon = copy.icon;
  return <span className={`request-chip request-${record.status}`}><Icon size={14} aria-hidden="true" />{copy.text}</span>;
}

// The mentee's next step with a mentor: ask, wait, or get on with booking.
export default function RequestMentorship({ mentor, record, onChanged }) {
  const [open, setOpen] = useState(false);
  const [motivation, setMotivation] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  async function send(event) {
    event.preventDefault();
    setSending(true);
    setError("");
    try {
      await apiRequest("/api/mentorships/", {
        method: "POST",
        body: JSON.stringify({ mentor_id: mentor.user_id, motivation: motivation.trim() }),
      });
      setOpen(false);
      setMotivation("");
      await onChanged?.();
    } catch (requestError) {
      setError(requestError.message || "Something went wrong. Please try again.");
    } finally {
      setSending(false);
    }
  }

  if (record?.status === "pending") {
    return (
      <div className="request-state">
        <p>Your request is with {mentor.full_name?.split(" ")[0] || "the mentor"}. You will be notified when they respond.</p>
        <Link to="/my-mentorships" className="btn btn-outline">View my requests</Link>
      </div>
    );
  }

  if (record?.status === "accepted") {
    return (
      <div className="request-state">
        <p>{mentor.full_name?.split(" ")[0] || "Your mentor"} accepted your request. Pick a time that works for you.</p>
        <div className="request-state-actions">
          <Link to="/booking" className="btn btn-primary"><CalendarClock size={16} aria-hidden="true" />Book a session</Link>
          <Link to="/chats" className="btn btn-outline"><MessageCircle size={16} aria-hidden="true" />Message</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="request-state">
      {record?.status === "declined" && <p>This request was declined. You are welcome to send a new one.</p>}
      <button type="button" className="btn btn-primary" onClick={() => { setOpen(!open); setError(""); }}>
        {open ? "Cancel" : record?.status === "declined" ? "Request again" : "Request mentorship"}
      </button>
      {open && (
        <form className="mentorship-motivation-form" onSubmit={send}>
          <label htmlFor={`motivation-${mentor.user_id}`}>What would you like to learn from this mentor?</label>
          <textarea
            id={`motivation-${mentor.user_id}`}
            value={motivation}
            onChange={(event) => setMotivation(event.target.value)}
            placeholder="Share your goals and what you hope to learn."
            minLength={20}
            maxLength={1000}
            rows={3}
            required
          />
          <p>{motivation.trim().length}/1000 characters (minimum 20)</p>
          <button type="submit" className="btn btn-primary" disabled={sending || motivation.trim().length < 20}>
            {sending ? "Sending request…" : "Send request"}
          </button>
        </form>
      )}
      {error && <p className="form-error" role="alert">{error}</p>}
    </div>
  );
}
