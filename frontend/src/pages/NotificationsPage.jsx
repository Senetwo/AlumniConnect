import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowRight, Bell, CalendarClock, Check, CheckCheck, Handshake, Megaphone, MessageCircle, UserPlus, UserRoundCheck, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import { FilterTabs, PageHeader } from "../components/dashboard";
import { apiRequest } from "../services/api";
import { getAuth } from "../services/authStorage";
import { timeAgo } from "../utils/format";

// A small icon per kind of update makes the list scannable at a glance.
function iconFor(item) {
  if (item.type === "mentorship_approved") return Check;
  if (item.type === "mentorship_rejected") return X;
  if (item.type.startsWith("mentorship")) return Handshake;
  if (item.type.startsWith("booking_") || item.resource_type === "booking") return CalendarClock;
  if (item.type === "new_message") return MessageCircle;
  if (item.type === "announcement") return Megaphone;
  if (item.type === "connection_request") return UserPlus;
  if (item.type === "connection_accepted" || item.type === "new_directory_member") return UserRoundCheck;
  return Bell;
}

function destinationFor(item, role) {
  if (item.type === "mentorship_request") return "/mentor-workspace";
  if (["mentorship_pending", "mentorship_approved", "mentorship_rejected", "mentorship_response"].includes(item.type)) return "/my-mentorships";
  if (item.type.startsWith("booking_") || item.resource_type === "booking") return "/booking";
  if (item.type === "new_message") return "/chats";
  if (["connection_request", "connection_accepted", "new_directory_member"].includes(item.type)) return "/directory";
  if (item.resource_type === "mentorship") return role === "mentor" ? "/mentor-workspace" : "/my-mentorships";
  return null;
}

const isToday = (iso) => new Date(iso).toDateString() === new Date().toDateString();

export default function NotificationsPage() {
  const user = getAuth()?.user;
  const role = user?.community_role || user?.role;
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updatingAll, setUpdatingAll] = useState(false);

  const loadNotifications = useCallback(async () => {
    setLoading(true); setError("");
    try { setNotifications(await apiRequest("/api/notifications/")); }
    catch (err) { setError(err.message || "Could not load notifications."); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { queueMicrotask(() => { void loadNotifications(); }); }, [loadNotifications]);

  const unreadCount = notifications.filter((item) => !item.read_at).length;
  const visible = notifications.filter((item) => filter === "all" || !item.read_at);
  const groups = useMemo(() => [
    { label: "Today", items: visible.filter((item) => isToday(item.created_at)) },
    { label: "Earlier", items: visible.filter((item) => !isToday(item.created_at)) },
  ].filter((group) => group.items.length), [visible]);

  async function markAsRead(id) {
    try {
      const updated = await apiRequest(`/api/notifications/${id}/read`, { method: "PATCH" });
      setNotifications((current) => current.map((item) => item.id === id ? updated : item));
      window.dispatchEvent(new Event("alumniconnect:notifications-updated"));
      return true;
    } catch (err) { setError(err.message || "Could not update notification."); return false; }
  }

  async function openNotification(item) {
    const destination = destinationFor(item, role);
    if (item.read_at || await markAsRead(item.id)) {
      if (destination) navigate(destination);
    }
  }

  async function markAllAsRead() {
    setUpdatingAll(true); setError("");
    try {
      await apiRequest("/api/notifications/read-all", { method: "PATCH" });
      const now = new Date().toISOString();
      setNotifications((current) => current.map((item) => ({ ...item, read_at: item.read_at || now })));
      window.dispatchEvent(new Event("alumniconnect:notifications-updated"));
    } catch (err) { setError(err.message || "Could not update notifications."); }
    finally { setUpdatingAll(false); }
  }

  return <div className="app"><Navbar /><main className="pg-page" style={{ maxWidth: 820 }}>
    <PageHeader
      eyebrow="YOUR UPDATES"
      title="Notifications"
      subtitle={unreadCount ? `${unreadCount} unread update${unreadCount === 1 ? "" : "s"}.` : "You are all caught up."}
      actions={<button type="button" className="btn btn-outline" onClick={markAllAsRead} disabled={!unreadCount || updatingAll}><CheckCheck size={16} aria-hidden="true" />{updatingAll ? "Updating…" : "Mark all as read"}</button>}
    />
    {error && <div role="alert" className="page-alert">{error}</div>}

    {loading ? <div className="pg-card pg-skeleton" role="status" aria-label="Loading notifications" /> : notifications.length === 0 ? (
      <section className="pg-card pg-empty">
        <Bell size={28} aria-hidden="true" />
        <h2>You are all caught up</h2>
        <p>Mentorship decisions, bookings, messages and community updates will show here.</p>
      </section>
    ) : (
      <div className="pg-main">
        <FilterTabs label="Filter notifications" value={filter} onChange={setFilter} options={[
          { id: "all", label: "All", count: notifications.length },
          { id: "unread", label: "Unread", count: unreadCount },
        ]} />
        {groups.length === 0 && <section className="pg-card pg-empty"><h3>No unread updates</h3><p>Switch to All to see earlier notifications.</p></section>}
        {groups.map((group) => (
          <section className="pg-main" key={group.label} aria-label={group.label}>
            <p className="pg-note-group">{group.label}</p>
            {group.items.map((item) => {
              const Icon = iconFor(item);
              const destination = destinationFor(item, role);
              return (
                <article key={item.id} className={`pg-card pg-notification ${item.read_at ? "is-read" : "is-unread"}`}>
                  <span className={`notification-type-icon ${item.read_at ? "is-read" : ""}`} role="img" aria-label={item.read_at ? "Read" : "Unread"}><Icon size={18} aria-hidden="true" /></span>
                  <div className="pg-notification-body">
                    <h3>{item.title}{!item.read_at && <span className="pg-new">New</span>}</h3>
                    <p>{item.message}</p>
                    <time dateTime={item.created_at} title={new Date(item.created_at).toLocaleString()}>{timeAgo(item.created_at)}</time>
                    <div className="pg-actions">
                      {destination && <button type="button" className="btn btn-outline" onClick={() => openNotification(item)}>View <ArrowRight size={14} aria-hidden="true" /></button>}
                      {!item.read_at && <button type="button" className="btn btn-outline" onClick={() => markAsRead(item.id)}>Mark as read</button>}
                    </div>
                  </div>
                </article>
              );
            })}
          </section>
        ))}
      </div>
    )}
  </main></div>;
}
