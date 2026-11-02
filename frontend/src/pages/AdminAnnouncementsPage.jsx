import { useState } from "react";
import { Megaphone } from "lucide-react";
import Navbar from "../components/Navbar";
import { apiRequest } from "../services/api";

export default function AdminAnnouncementsPage() {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function submit(event) {
    event.preventDefault(); setBusy(true); setError(""); setSuccess("");
    try {
      const result = await apiRequest("/api/admin/announcements", { method: "POST", body: JSON.stringify({ title, body }) });
      setSuccess(`Announcement sent to ${result.recipient_count} members.`);
      setTitle(""); setBody("");
    } catch (err) { setError(err.message || "Unable to publish announcement."); }
    finally { setBusy(false); }
  }

  return <div className="app"><Navbar /><main className="app-content-page admin-knowledge-page">
    <header className="content-page-heading"><div className="flex items-center gap-2 text-sm font-medium text-red-700"><Megaphone size={18} /> Administration</div><h1>Community announcements</h1><p>Send an announcement to members. It will appear in their notification inbox.</p></header>
    {error && <div role="alert" className="content-alert content-alert-error">{error}</div>}
    {success && <div role="status" className="content-alert content-alert-success">{success}</div>}
    <form className="content-panel space-y-5" onSubmit={submit}>
      <label className="block text-sm font-medium text-slate-700">Announcement title<input className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5" value={title} onChange={(event) => setTitle(event.target.value)} minLength={3} maxLength={160} required /></label>
      <label className="block text-sm font-medium text-slate-700">Message<textarea className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5" value={body} onChange={(event) => setBody(event.target.value)} minLength={10} maxLength={4000} rows={6} required /></label>
      <p className="text-sm text-slate-500">This sends one notification to every current member account. Review the recipient count before publishing.</p>
      <button className="btn btn-primary" disabled={busy}>{busy ? "Sending…" : "Send announcement"}</button>
    </form>
  </main></div>;
}
