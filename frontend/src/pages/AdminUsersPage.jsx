import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Search, ShieldCheck, SlidersHorizontal, UserRound, Users } from "lucide-react";
import Navbar from "../components/Navbar";
import { apiRequest } from "../services/api";
import { displayEmail } from "../utils/format";

const initials = name => name?.trim().split(/\s+/).slice(0, 2).map(part => part[0]).join("").toUpperCase() || "U";

export default function AdminUsersPage() {
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("all");
  const [status, setStatus] = useState("all");
  const [data, setData] = useState({ items: [], total: 0 });
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const query = new URLSearchParams({ search, role, status, offset: String(offset), limit: "25" });
      setData(await apiRequest(`/api/admin/users?${query}`));
    } catch (requestError) {
      setError(requestError.message || "Unable to load accounts.");
    } finally {
      setLoading(false);
    }
  }, [search, role, status, offset]);

  useEffect(() => { queueMicrotask(() => { void load(); }); }, [load]);

  async function toggleActive(user) {
    const next = !user.is_active;
    if (!window.confirm(`${next ? "Reactivate" : "Suspend"} ${user.full_name}'s account?`)) return;
    setBusyId(user.id);
    try {
      await apiRequest(`/api/admin/users/${user.id}/status`, { method: "PATCH", body: JSON.stringify({ is_active: next }) });
      await load();
    } catch (requestError) {
      setError(requestError.message || "Account status could not be changed.");
    } finally { setBusyId(null); }
  }

  async function changeRole(user, next) {
    if (!window.confirm(`Change ${user.full_name}'s platform role to ${next}? This permission change will be audited.`)) return;
    setBusyId(user.id);
    try {
      await apiRequest(`/api/admin/users/${user.id}/role`, { method: "PATCH", body: JSON.stringify({ role: next }) });
      await load();
    } catch (requestError) {
      setError(requestError.message || "Role could not be changed.");
    } finally { setBusyId(null); }
  }

  const first = data.total === 0 ? 0 : offset + 1;
  const last = Math.min(offset + data.items.length, data.total);

  return (
    <div className="app admin-app">
      <Navbar />
      <main className="app-content-page admin-tool-page">
        <header className="admin-tool-heading">
          <div><div className="admin-eyebrow"><Users size={15} /> ADMIN CONSOLE <span className="admin-eyebrow-dot" /> DIRECTORY</div><h1>Members</h1><p>Find an account, review its status, and manage access safely.</p></div>
          <div className="admin-members-total"><span className="admin-total-icon"><UserRound size={17} /></span><span><strong>{loading ? "—" : data.total.toLocaleString()}</strong><small>matching accounts</small></span></div>
        </header>

        {error && <div role="alert" className="admin-error-banner"><span>{error}</span><button type="button" onClick={() => void load()}>Try again</button></div>}

        <section className="admin-member-browser">
          <div className="admin-member-toolbar">
            <label className="admin-search-box"><Search size={17} /><span className="sr-only">Search members by name or email</span><input placeholder="Search name or email" value={search} onChange={event => { setSearch(event.target.value); setOffset(0); }} /></label>
            <div className="admin-filter-label"><SlidersHorizontal size={15} /><span>Filter</span></div>
            <label className="admin-filter-select"><span className="sr-only">Filter by role</span><select value={role} onChange={event => { setRole(event.target.value); setOffset(0); }}><option value="all">All roles</option><option value="mentor">Mentor</option><option value="mentee">Mentee</option><option value="admin">Admin</option></select></label>
            <label className="admin-filter-select"><span className="sr-only">Filter by account status</span><select value={status} onChange={event => { setStatus(event.target.value); setOffset(0); }}><option value="all">All statuses</option><option value="active">Active</option><option value="suspended">Suspended</option></select></label>
          </div>

          <div className="admin-member-table-wrap">
            <table className="admin-table admin-member-table">
              <thead><tr><th>Member</th><th>Role</th><th>Account status</th><th>Verification</th><th>Joined</th><th><span className="sr-only">Account actions</span></th></tr></thead>
              <tbody>
                {loading && !data.items.length && <tr><td colSpan="6" className="admin-table-message">Loading member accounts…</td></tr>}
                {!loading && data.items.map(user => <tr key={user.id}>
                  <td><div className="admin-member-identity"><span className="admin-member-avatar">{initials(user.full_name)}</span><span className="admin-member-name"><strong>{user.full_name}</strong><small>{displayEmail(user.email)}</small></span></div></td>
                  <td><div className="admin-role-cell"><span className={`admin-role-pill role-${user.role}`}>{user.role}</span>{user.community_role && user.role === "admin" && <small>Community: {user.community_role}</small>}</div></td>
                  <td><span className={`admin-status-pill ${user.is_active ? "status-active" : "status-suspended"}`}><i />{user.is_active ? "Active" : "Suspended"}</span></td>
                  <td><span className={`admin-verification ${user.is_email_verified ? "verified" : "unverified"}`}><i />{user.is_email_verified ? "Verified" : "Unverified"}</span></td>
                  <td className="admin-date-cell">{new Date(user.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}</td>
                  <td><div className="admin-member-actions"><select aria-label={`Change role for ${user.full_name}`} value="" disabled={busyId === user.id || user.role === "admin"} onChange={event => { if (event.target.value) void changeRole(user, event.target.value); }}><option value="" disabled>{user.role === "admin" ? "Admin" : "Change role"}</option><option value="mentor">Mentor</option><option value="mentee">Mentee</option><option value="admin">Grant admin</option></select><button type="button" disabled={busyId === user.id} className={user.is_active ? "admin-suspend-action" : "admin-reactivate-action"} onClick={() => void toggleActive(user)}>{busyId === user.id ? "Saving…" : user.is_active ? "Suspend" : "Reactivate"}</button></div></td>
                </tr>)}
                {!loading && !data.items.length && <tr><td colSpan="6" className="admin-table-message"><span className="admin-empty-icon"><Users size={20} /></span><strong>No matching members</strong><small>Try a different name, role, or account status.</small></td></tr>}
              </tbody>
            </table>
          </div>

          <footer className="admin-table-footer"><span>Showing <strong>{first}–{last}</strong> of <strong>{data.total}</strong></span><div><button type="button" aria-label="Previous page" disabled={offset === 0 || loading} onClick={() => setOffset(Math.max(0, offset - 25))}><ArrowLeft size={15} />Previous</button><button type="button" aria-label="Next page" disabled={offset + 25 >= data.total || loading} onClick={() => setOffset(offset + 25)}>Next<ArrowRight size={15} /></button></div></footer>
        </section>
        <p className="admin-security-note"><ShieldCheck size={15} /> Role and account changes are recorded in the admin audit history. Suspension is reversible; accounts are not deleted here.</p>
      </main>
    </div>
  );
}
