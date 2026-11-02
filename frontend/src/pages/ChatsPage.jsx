import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, CalendarClock, MessageCircle, Search, Send } from "lucide-react";
import Navbar from "../components/Navbar";
import { getAuth } from "../services/authStorage";
import { apiRequest } from "../services/api";
import { initials } from "../utils/format";

const MAX_LENGTH = 5000;

function listTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (date.toDateString() === new Date().toDateString()) {
    return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  }
  return date.toLocaleDateString([], { month: "short", day: "numeric" });
}

function dayLabel(value) {
  const date = new Date(value);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);
  if (date.toDateString() === today.toDateString()) return "Today";
  if (date.toDateString() === yesterday.toDateString()) return "Yesterday";
  return date.toLocaleDateString([], { weekday: "long", day: "numeric", month: "long" });
}

const messagesPath = (item) =>
  item.kind === "mentorship" ? `/api/chat/conversations/${item.id}/messages` : `/api/connections/${item.id}/messages`;

export default function ChatsPage() {
  const user = getAuth()?.user;
  const isMentor = (user?.community_role || user?.role) === "mentor";
  const [mentorshipChats, setMentorshipChats] = useState([]);
  const [connections, setConnections] = useState([]);
  const [selectedKey, setSelectedKey] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const listRef = useRef(null);
  const composerRef = useRef(null);

  const items = useMemo(() => {
    const mentorship = mentorshipChats.map((chat) => ({
      key: `m-${chat.id}`,
      kind: "mentorship",
      id: chat.id,
      name: isMentor ? chat.mentee_name : chat.mentor_name,
      photo: isMentor ? chat.mentee_profile_picture_url : chat.mentor_profile_picture_url,
      preview: chat.latest_message || "Start your conversation",
      at: chat.latest_message_at || chat.created_at,
      unread: chat.unread_count || 0,
    })).sort((a, b) => new Date(b.at) - new Date(a.at));
    const community = connections.map((connection) => ({
      key: `c-${connection.id}`,
      kind: "connection",
      id: connection.id,
      name: connection.other_user?.full_name || "AlumniConnect member",
      photo: null,
      preview: "Community connection",
      at: null,
      unread: 0,
    }));
    return [...mentorship, ...community];
  }, [mentorshipChats, connections, isMentor]);

  const loadInbox = useCallback(async () => {
    try {
      const [chats, rows] = await Promise.all([
        apiRequest("/api/chat/conversations"),
        apiRequest("/api/connections").catch(() => []),
      ]);
      setMentorshipChats(chats);
      setConnections(rows.filter((row) => row.status === "accepted"));
      setError("");
    } catch (err) {
      setError(err.message || "Unable to load your conversations. Reconnecting…");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { queueMicrotask(() => { void loadInbox(); }); }, [loadInbox]);

  useEffect(() => {
    const interval = window.setInterval(() => {
      if (document.visibilityState === "visible") void loadInbox();
    }, 12000);
    return () => window.clearInterval(interval);
  }, [loadInbox]);

  // On a wide screen open the most recent conversation so the thread is never an empty pane.
  useEffect(() => {
    queueMicrotask(() => {
      setSelectedKey((current) => {
        if (current && items.some((item) => item.key === current)) return current;
        return window.innerWidth > 900 && items.length ? items[0].key : null;
      });
    });
  }, [items]);

  const selected = items.find((item) => item.key === selectedKey) || null;

  const loadMessages = useCallback(async (item, { quiet = false } = {}) => {
    if (!item) { setMessages([]); return; }
    if (!quiet) setMessagesLoading(true);
    try {
      setMessages(await apiRequest(messagesPath(item)));
      setError("");
      if (!quiet) void loadInbox();
    } catch (err) {
      if (!quiet) setMessages([]);
      setError(err.message || "Unable to load messages. Reconnecting…");
    } finally {
      if (!quiet) setMessagesLoading(false);
    }
  }, [loadInbox]);

  // Short polling keeps both people up to date without a second transport. The API
  // rechecks membership on every read.
  const selectedId = selected?.key;
  useEffect(() => {
    if (!selected) return undefined;
    queueMicrotask(() => { void loadMessages(selected); });
    const refresh = () => {
      if (document.visibilityState === "visible") void loadMessages(selected, { quiet: true });
    };
    const interval = window.setInterval(refresh, 3000);
    window.addEventListener("focus", refresh);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener("focus", refresh);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId, loadMessages]);

  useEffect(() => {
    const list = listRef.current;
    if (list) list.scrollTop = list.scrollHeight;
  }, [messages, selectedId]);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    return term ? items.filter((item) => item.name.toLowerCase().includes(term)) : items;
  }, [items, search]);

  async function send(event) {
    event?.preventDefault();
    const body = draft.trim();
    if (!selected || !body || sending) return;
    setSending(true);
    setError("");
    try {
      const message = await apiRequest(messagesPath(selected), { method: "POST", body: JSON.stringify({ body }) });
      setMessages((current) => [...current, message]);
      setDraft("");
      if (composerRef.current) composerRef.current.style.height = "auto";
      void loadInbox();
    } catch (err) {
      setError(err.message || "Unable to send message. Your draft is still here.");
    } finally {
      setSending(false);
    }
  }

  function onKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void send();
    }
  }

  function onInput(event) {
    setDraft(event.target.value);
    event.target.style.height = "auto";
    event.target.style.height = `${Math.min(event.target.scrollHeight, 140)}px`;
  }

  return (
    <div className="app">
      <Navbar />
      <main className="ch-page">
        <header className="ch-heading">
          <span className="eyebrow">MESSAGES</span>
          <h1>Your conversations</h1>
        </header>

        {error && <div className="page-alert" role="alert">{error}</div>}

        {loading ? (
          <div className="ch-card ch-loading" role="status">Loading your conversations…</div>
        ) : (
          <div className={`ch-layout ${selected ? "has-selected" : ""}`}>
            <aside className="ch-card ch-side" aria-label="Conversations">
              <label className="ch-search">
                <Search size={16} aria-hidden="true" />
                <span className="visually-hidden">Search conversations</span>
                <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search people" />
              </label>
              {filtered.length === 0 ? (
                <div className="ch-list-empty">
                  <p>{items.length ? "No matches found" : "No conversations yet"}</p>
                  <span>{items.length ? "Try another name." : "When a mentor accepts your request, or a community member accepts your connection, your conversation appears here."}</span>
                </div>
              ) : (
                <ul className="ch-list">
                  {filtered.map((item) => (
                    <li key={item.key}>
                      <button type="button" className={`ch-item ${selectedKey === item.key ? "is-selected" : ""}`} onClick={() => setSelectedKey(item.key)} aria-current={selectedKey === item.key ? "true" : undefined}>
                        <span className="ch-avatar" aria-hidden="true">{item.photo ? <img src={item.photo} alt="" /> : initials(item.name)}</span>
                        <span className="ch-item-copy">
                          <strong>{item.name}</strong>
                          <small>{item.preview}</small>
                          <em>{item.kind === "mentorship" ? "Mentorship" : "Connection"}</em>
                        </span>
                        <span className="ch-item-meta">
                          <time>{listTime(item.at)}</time>
                          {item.unread > 0 && <b aria-label={`${item.unread} unread messages`}>{item.unread}</b>}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </aside>

            <section className="ch-card ch-thread" aria-label="Message thread">
              {!selected ? (
                <div className="ch-thread-empty">
                  <span><MessageCircle size={26} aria-hidden="true" /></span>
                  <h2>Select a conversation</h2>
                  <p>Pick someone from the list to read and reply.</p>
                </div>
              ) : (
                <>
                  <header className="ch-head">
                    <button className="ch-back" type="button" onClick={() => setSelectedKey(null)} aria-label="Back to conversations"><ArrowLeft size={18} aria-hidden="true" /></button>
                    <span className="ch-avatar large" aria-hidden="true">{selected.photo ? <img src={selected.photo} alt="" /> : initials(selected.name)}</span>
                    <div className="ch-head-person">
                      <h2>{selected.name}</h2>
                      <p>{selected.kind === "mentorship" ? "Accepted mentorship · private chat" : "Community connection"}</p>
                    </div>
                    {selected.kind === "mentorship" && (
                      <Link to="/booking" className="btn btn-outline ch-book"><CalendarClock size={16} aria-hidden="true" />Book a session</Link>
                    )}
                  </header>

                  <div className="ch-messages" aria-live="polite" ref={listRef}>
                    {messagesLoading ? <p className="ch-note">Loading messages…</p> : messages.length === 0 ? <p className="ch-note">No messages yet. Say hello to {selected.name.split(" ")[0]}.</p> : messages.map((message, index) => {
                      const showDay = index === 0 || new Date(message.created_at).toDateString() !== new Date(messages[index - 1].created_at).toDateString();
                      const mine = message.sender_id === user?.id;
                      return (
                        <div key={message.id} className="ch-row">
                          {showDay && <div className="ch-day"><span>{dayLabel(message.created_at)}</span></div>}
                          <article className={`ch-bubble ${mine ? "is-mine" : "is-theirs"}`}>
                            <p>{message.body}</p>
                            <time dateTime={message.created_at}>{new Date(message.created_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}</time>
                          </article>
                        </div>
                      );
                    })}
                  </div>

                  <form className="ch-compose" onSubmit={send}>
                    <label className="visually-hidden" htmlFor="ch-message">Message</label>
                    <textarea
                      id="ch-message"
                      ref={composerRef}
                      value={draft}
                      onChange={onInput}
                      onKeyDown={onKeyDown}
                      placeholder="Write a message…  (Enter to send, Shift+Enter for a new line)"
                      maxLength={MAX_LENGTH}
                      rows={1}
                      disabled={sending}
                    />
                    <button className="btn btn-primary" type="submit" aria-label={sending ? "Sending message" : "Send message"} disabled={!draft.trim() || sending}>
                      <Send size={17} aria-hidden="true" /><span>{sending ? "Sending…" : "Send"}</span>
                    </button>
                  </form>
                </>
              )}
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
