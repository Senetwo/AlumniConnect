import { useCallback, useEffect, useState } from "react";
import { Activity, ArrowRight, Flag, Handshake, RefreshCw, ShieldCheck, UserRound } from "lucide-react";
import Navbar from "../components/Navbar";
import { apiRequest } from "../services/api";

const dateTime = value => value ? new Date(value).toLocaleString(undefined, { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" }) : "—";

export default function AdminOperationsPage() {
  const [tab, setTab] = useState("mentorships");
  const [mentorships, setMentorships] = useState({ items: [], total: 0 });
  const [reports, setReports] = useState([]);
  const [audit, setAudit] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [updatingReport, setUpdatingReport] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [mentorshipData, reportData, auditData, dashboardData] = await Promise.all([
        apiRequest("/api/admin/mentorships?limit=100"),
        apiRequest("/api/admin/reports"),
        apiRequest("/api/admin/audit?limit=100"),
        apiRequest("/api/admin/dashboard"),
      ]);
      setMentorships(mentorshipData);
      setReports(reportData);
      setAudit(auditData);
      setMetrics(dashboardData.metrics);
    } catch (requestError) {
      setError(requestError.message || "Unable to load operational data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { queueMicrotask(() => { void load(); }); }, [load]);

  async function updateReport(id, status) {
    setUpdatingReport(id);
    setError("");
    try {
      await apiRequest(`/api/admin/reports/${id}?status=${status}`, { method: "PATCH" });
      await load();
    } catch (requestError) {
      setError(requestError.message || "Report status could not be updated.");
    } finally { setUpdatingReport(null); }
  }

  const openReports = metrics?.open_reports ?? reports.filter(report => report.status === "open").length;
  const pendingMentorships = metrics?.mentorships?.pending ?? mentorships.items.filter(item => item.status === "pending").length;
  const tabs = [
    { id: "mentorships", label: "Mentorships", count: mentorships.total, icon: Handshake },
    { id: "reports", label: "Member reports", count: openReports, icon: Flag, countLabel: "open" },
    { id: "audit", label: "Admin history", count: audit.length, icon: Activity },
  ];

  return (
    <div className="app admin-app">
      <Navbar />
      <main className="app-content-page admin-tool-page">
        <header className="admin-tool-heading">
          <div><div className="admin-eyebrow"><ShieldCheck size={15} /> ADMIN CONSOLE <span className="admin-eyebrow-dot" /> WORKFLOW REVIEW</div><h1>Operations</h1><p>Monitor mentorship requests and review member reports. Private conversations are not available here.</p></div>
          <button type="button" className="admin-refresh-button" disabled={loading} onClick={() => void load()}><RefreshCw size={16} className={loading ? "admin-spin" : ""} />{loading ? "Refreshing" : "Refresh"}</button>
        </header>

        {error && <div role="alert" className="admin-error-banner"><span>{error}</span><button type="button" onClick={() => void load()}>Try again</button></div>}

        <section className="admin-ops-summary" aria-label="Operations summary">
          <article><span className="admin-ops-summary-icon tone-violet"><Handshake size={17} /></span><span><strong>{loading ? "—" : mentorships.total}</strong><small>Mentorship requests</small></span></article>
          <article><span className="admin-ops-summary-icon tone-amber"><Flag size={17} /></span><span><strong>{loading ? "—" : openReports}</strong><small>Open member reports</small></span></article>
          <article><span className="admin-ops-summary-icon tone-blue"><Activity size={17} /></span><span><strong>{loading ? "—" : pendingMentorships}</strong><small>Pending mentorship requests</small></span></article>
          <article><span className="admin-ops-summary-icon tone-green"><ShieldCheck size={17} /></span><span><strong>{loading ? "—" : (metrics?.match_feedback?.average_rating ?? "—")}</strong><small>Match rating ({metrics?.match_feedback?.count ?? 0} responses)</small></span></article>
        </section>

        <section className="admin-ops-workspace">
          <div className="admin-ops-tabs" role="tablist" aria-label="Operations sections">
            {tabs.map(({ id, label, count, icon: Icon, countLabel }) => <button key={id} id={`ops-tab-${id}`} type="button" role="tab" aria-selected={tab === id} aria-controls={`ops-panel-${id}`} className={tab === id ? "is-selected" : ""} onClick={() => setTab(id)}><Icon size={16} /><span>{label}</span><span className={`admin-tab-count ${id === "reports" && count > 0 ? "has-items" : ""}`}>{loading ? "—" : countLabel === "open" ? `${count} open` : count}</span></button>)}
          </div>

          <div className="admin-ops-panel" role="tabpanel" id={`ops-panel-${tab}`} aria-labelledby={`ops-tab-${tab}`}>
            {tab === "mentorships" && <>
              <div className="admin-ops-panel-heading"><div><h2>Mentorship requests</h2><p>Current request status and participants</p></div><span className="admin-panel-tag">{mentorships.total} total</span></div>
              <div className="admin-table-scroll"><table className="admin-table"><thead><tr><th>Mentee</th><th>Mentor</th><th>Status</th><th>Requested</th></tr></thead><tbody>
                {loading && !mentorships.items.length && <tr><td colSpan="4" className="admin-table-message">Loading mentorship activity…</td></tr>}
                {!loading && mentorships.items.map(item => <tr key={item.id}><td><span className="admin-name-cell"><span className="admin-small-avatar">{item.mentee?.[0]?.toUpperCase() || "M"}</span>{item.mentee}</span></td><td>{item.mentor}</td><td><span className={`admin-status-pill status-${item.status}`}><i />{item.status}</span></td><td className="admin-date-cell">{dateTime(item.created_at)}</td></tr>)}
                {!loading && !mentorships.items.length && <tr><td colSpan="4" className="admin-table-message"><span className="admin-empty-icon"><Handshake size={20} /></span><strong>No mentorship requests</strong><small>Requests will appear here as members connect.</small></td></tr>}
              </tbody></table></div>
              <div className="admin-ops-table-footnote">This view contains request metadata only. Mentorship messages remain private.</div>
            </>}

            {tab === "reports" && <>
              <div className="admin-ops-panel-heading"><div><h2>Member reports</h2><p>Review a report and update its moderation status</p></div><span className={`admin-panel-tag ${openReports ? "admin-tag-attention" : ""}`}>{openReports} open</span></div>
              <div className="admin-table-scroll"><table className="admin-table admin-report-table"><thead><tr><th>Reason</th><th>Report details</th><th>Received</th><th>Status</th></tr></thead><tbody>
                {loading && !reports.length && <tr><td colSpan="4" className="admin-table-message">Loading member reports…</td></tr>}
                {!loading && reports.map(report => <tr key={report.id}><td><span className="admin-report-reason"><Flag size={14} />{report.reason}</span></td><td className="admin-report-details">{report.details || <span className="admin-muted">No additional details provided</span>}</td><td className="admin-date-cell">{dateTime(report.created_at)}</td><td><label className="sr-only" htmlFor={`report-status-${report.id}`}>Update report status</label><select id={`report-status-${report.id}`} className="admin-report-status" value={report.status} disabled={updatingReport === report.id} onChange={event => void updateReport(report.id, event.target.value)}><option value="open">Open</option><option value="reviewed">Reviewed</option><option value="resolved">Resolved</option></select></td></tr>)}
                {!loading && !reports.length && <tr><td colSpan="4" className="admin-table-message"><span className="admin-empty-icon"><Flag size={20} /></span><strong>No reports have been submitted</strong><small>Member reports will appear here for review.</small></td></tr>}
              </tbody></table></div>
              <div className="admin-ops-table-footnote">Report details are visible to administrators for moderation. Private messages are not included.</div>
            </>}

            {tab === "audit" && <>
              <div className="admin-ops-panel-heading"><div><h2>Administrative history</h2><p>Recent audited account and moderation changes</p></div><span className="admin-panel-tag">Latest {audit.length}</span></div>
              {loading && !audit.length ? <div className="admin-table-message">Loading admin history…</div> : audit.length ? <ol className="admin-audit-list">{audit.map(row => <li key={row.id}><span className="admin-audit-icon"><ShieldCheck size={16} /></span><div className="admin-audit-copy"><strong>{row.action.replaceAll("_", " ")}</strong><p><UserRound size={13} />{row.actor}<ArrowRight size={12} />{row.target}{row.details ? <span className="admin-audit-details">{row.details}</span> : null}</p></div><time>{dateTime(row.created_at)}</time></li>)}</ol> : <div className="admin-table-message"><span className="admin-empty-icon"><Activity size={20} /></span><strong>No administrative actions recorded</strong><small>Audited changes will be listed here.</small></div>}
            </>}
          </div>
        </section>
      </main>
    </div>
  );
}
