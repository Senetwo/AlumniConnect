import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  CalendarDays,
  Flag,
  Handshake,
  Megaphone,
  RefreshCw,
  ShieldCheck,
  Users,
} from "lucide-react";
import Navbar from "../components/Navbar";
import { apiRequest } from "../services/api";

const formatNumber = value => value == null ? "—" : new Intl.NumberFormat().format(value);
const dateLabel = value => value ? new Date(`${value}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" }) : "—";

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setData(await apiRequest("/api/admin/dashboard"));
    } catch (requestError) {
      setError(requestError.message || "Unable to load dashboard metrics.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { queueMicrotask(() => { void load(); }); }, [load]);

  const metrics = data?.metrics;
  const registrations = data?.registration_trend || [];
  const largestDay = Math.max(1, ...registrations.map(day => day.count));
  const cards = [
    { label: "Community members", value: metrics?.total_members, description: "Registered member accounts", icon: Users, tone: "blue" },
    { label: "New members", value: metrics?.new_members_30d, description: "Joined in the last 30 days", icon: Activity, tone: "green" },
    { label: "Accepted mentorships", value: metrics?.active_mentorships, description: "Current accepted requests", icon: Handshake, tone: "violet" },
    { label: "Open reports", value: metrics?.open_reports, description: "Awaiting admin review", icon: Flag, tone: "amber", href: "/admin/operations" },
  ];

  const attentionItems = [
    { label: "Mentorship requests", detail: "Waiting for a mentor response", count: metrics?.mentorships?.pending, href: "/admin/operations", icon: Handshake },
    { label: "Member reports", detail: "Open moderation reports", count: metrics?.open_reports, href: "/admin/operations", icon: Flag },
    { label: "Knowledge drafts", detail: "Resources not yet published", count: metrics?.draft_resources, href: "/admin-knowledge", icon: BookOpen },
  ];

  return (
    <div className="app admin-app">
      <Navbar />
      <main className="app-content-page admin-dashboard-page">
        <header className="admin-dashboard-heading">
          <div>
            <div className="admin-eyebrow"><ShieldCheck size={15} /> ADMIN CONSOLE <span className="admin-eyebrow-dot" /> PLATFORM OVERVIEW</div>
            <h1>Good to see you.</h1>
            <p>Here’s what’s happening across your alumni community.</p>
          </div>
          <div className="admin-heading-actions">
            <div className="admin-period-chip"><CalendarDays size={15} /><span>Last 30 days</span></div>
            <button type="button" onClick={() => void load()} disabled={loading} className="admin-refresh-button">
              <RefreshCw size={16} className={loading ? "admin-spin" : ""} />
              <span>{loading ? "Refreshing" : "Refresh"}</span>
            </button>
          </div>
        </header>

        {error && <div role="alert" className="admin-error-banner"><span>{error}</span><button type="button" onClick={() => void load()}>Try again</button></div>}

        <section className="admin-metric-grid" aria-label="Community metrics">
          {cards.map(({ label, value, description, icon: Icon, tone, href }) => {
            const content = <>
              <div className="admin-metric-top"><span className={`admin-metric-icon tone-${tone}`}><Icon size={19} /></span>{href && <ArrowUpRight size={16} className="admin-metric-link-icon" />}</div>
              <span className="admin-metric-label">{label}</span>
              <strong className="admin-metric-value">{loading ? <span className="admin-skeleton" /> : formatNumber(value)}</strong>
              <span className="admin-metric-description">{description}</span>
            </>;
            return href
              ? <Link to={href} className="admin-metric-card admin-metric-card-link" key={label}>{content}</Link>
              : <article className="admin-metric-card" key={label}>{content}</article>;
          })}
        </section>

        <div className="admin-dashboard-columns">
          <section className="admin-surface admin-trend-panel">
            <div className="admin-panel-heading">
              <div><h2>Member growth</h2><p>New registrations by day</p></div>
              <span className="admin-panel-tag">30-day trend</span>
            </div>
            {loading ? <div className="admin-chart-loading" aria-label="Loading registration trend" /> : registrations.length ? <>
              <div className="admin-chart-summary"><strong>{formatNumber(metrics?.new_members_30d)}</strong><span>registrations in this period</span></div>
              <div className="admin-chart" role="img" aria-label="Daily new member registrations over the last 30 days">
                {registrations.map(day => <div className="admin-chart-column" key={day.date} title={`${dateLabel(day.date)}: ${day.count} registrations`}><span className="admin-chart-bar" style={{ height: `${day.count ? Math.max(9, day.count / largestDay * 100) : 2}%` }} /></div>)}
              </div>
              <div className="admin-chart-axis"><span>{dateLabel(registrations[0]?.date)}</span><span>{dateLabel(registrations[Math.floor(registrations.length / 2)]?.date)}</span><span>{dateLabel(registrations.at(-1)?.date)}</span></div>
            </> : <div className="admin-empty-chart">Registration activity will appear here when accounts are created.</div>}
            <p className="admin-chart-footnote">Counts are based on member account creation dates. This chart does not imply an increase or decrease in engagement.</p>
          </section>

          <section className="admin-surface admin-attention-panel">
            <div className="admin-panel-heading">
              <div><h2>Needs attention</h2><p>Queues that may need a review</p></div>
              <span className="admin-attention-icon"><Flag size={17} /></span>
            </div>
            <div className="admin-attention-list">
              {attentionItems.map(({ label, detail, count, href, icon: Icon }) => (
                <Link to={href} className="admin-attention-row" key={label}>
                  <span className="admin-attention-row-icon"><Icon size={17} /></span>
                  <span className="admin-attention-copy"><strong>{label}</strong><small>{detail}</small></span>
                  <span className={`admin-queue-count ${count > 0 ? "has-items" : ""}`}>{loading ? "—" : formatNumber(count)}</span>
                  <ArrowRight size={15} className="admin-attention-arrow" />
                </Link>
              ))}
            </div>
            <Link className="admin-panel-footer-link" to="/admin/operations">Open operations <ArrowRight size={15} /></Link>
          </section>
        </div>

        <section className="admin-lower-grid" aria-label="Platform activity summary">
          <article className="admin-surface admin-activity-card">
            <div className="admin-activity-icon tone-blue"><BookOpen size={18} /></div>
            <div className="admin-activity-content"><span>Knowledge Hub</span><strong>{loading ? "—" : `${formatNumber(metrics?.published_resources)} published`}</strong><small>{loading ? "Loading resource counts" : `${formatNumber(metrics?.draft_resources)} drafts · views not tracked`}</small></div>
            <Link to="/admin-knowledge" aria-label="Manage Knowledge Hub"><ArrowUpRight size={17} /></Link>
          </article>
          <article className="admin-surface admin-activity-card">
            <div className="admin-activity-icon tone-green"><Users size={18} /></div>
            <div className="admin-activity-content"><span>Community connections</span><strong>{loading ? "—" : formatNumber(metrics?.community_connections_30d)}</strong><small>Connection requests in the last 30 days</small></div>
            <Link to="/directory" aria-label="Open the community directory"><ArrowUpRight size={17} /></Link>
          </article>
          <article className="admin-surface admin-activity-card admin-untracked-card">
            <div className="admin-activity-icon tone-gray"><Activity size={18} /></div>
            <div className="admin-activity-content"><span>Active members</span><strong>Not tracked</strong><small>Last activity data is not collected</small></div>
            <span className="admin-untracked-indicator"><ArrowDownRight size={15} />Data gap</span>
          </article>
        </section>

        <section className="admin-quick-actions">
          <div><span className="admin-quick-kicker">ADMIN TOOLS</span><h2>Quick actions</h2></div>
          <div className="admin-quick-links">
            <Link to="/admin/users"><Users size={17} /><span>Manage members</span><ArrowRight size={15} /></Link>
            <Link to="/admin-announcements"><Megaphone size={17} /><span>New announcement</span><ArrowRight size={15} /></Link>
            <Link to="/admin-knowledge"><BookOpen size={17} /><span>Manage resources</span><ArrowRight size={15} /></Link>
          </div>
        </section>
      </main>
    </div>
  );
}
