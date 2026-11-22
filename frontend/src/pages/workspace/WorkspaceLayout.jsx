import { useCallback, useEffect, useState } from "react";
import { Link, NavLink, Outlet, useParams } from "react-router-dom";
import { ArrowLeft, MessageCircle } from "lucide-react";
import Navbar from "../../components/Navbar";
import { PageHeader } from "../../components/dashboard";
import { apiRequest } from "../../services/api";
import { initials } from "../../utils/format";
import { StatusChip, Loading } from "./ui";

const sections = [
  { to: "", label: "Overview", end: true },
  { to: "sessions", label: "Sessions", count: (p) => p.sessions.upcoming },
  { to: "notes", label: "Meeting notes" },
  { to: "goals", label: "Goals & tasks", count: (p) => p.action_items.open },
  { to: "progress", label: "Progress history" },
];

export default function WorkspaceLayout() {
  const { mentorshipId } = useParams();
  const [workspace, setWorkspace] = useState(null);
  const [error, setError] = useState("");
  const base = `/api/mentorships/${mentorshipId}`;

  const reload = useCallback(async () => {
    try {
      setWorkspace(await apiRequest(`${base}/workspace`));
      setError("");
    } catch (err) {
      setError(err.message || "Unable to load this workspace.");
    }
  }, [base]);

  useEffect(() => { queueMicrotask(() => { void reload(); }); }, [reload]);

  const isMentor = workspace?.viewer.role === "mentor";
  const backTo = isMentor ? "/mentor-workspace" : "/my-mentorships";
  const partner = workspace && (isMentor ? workspace.mentee : workspace.mentor);

  return (
    <div className="app">
      <Navbar />
      <main className="pg-page ws-page">
        <Link to={backTo} className="ws-back"><ArrowLeft size={16} aria-hidden="true" />{isMentor ? "Mentor dashboard" : "My mentorships"}</Link>

        {error && (
          <div className="pg-card pg-empty">
            <h2>Workspace unavailable</h2>
            <p>{error} Only the mentor and mentee of an accepted mentorship can open its workspace.</p>
            <Link to={backTo} className="btn btn-primary">Go back</Link>
          </div>
        )}

        {!error && !workspace && <Loading text="Loading workspace" />}

        {workspace && (
          <>
            <PageHeader
              eyebrow="MENTORSHIP WORKSPACE"
              title={isMentor ? `Mentoring ${workspace.mentee.full_name}` : `Mentored by ${workspace.mentor.full_name}`}
              subtitle={workspace.status === "completed" ? "This mentorship is completed. Everything below is kept as a read-only record." : "Plan sessions, keep notes, set goals and track what gets done."}
              actions={<>
                <StatusChip value={workspace.status}>{workspace.status === "completed" ? "Completed" : "Active"}</StatusChip>
                <Link to="/chats" className="btn btn-outline"><MessageCircle size={16} aria-hidden="true" />Message {partner.full_name.split(" ")[0]}</Link>
              </>}
            />
            <nav className="ws-tabs" aria-label="Workspace sections">
              {sections.map((section) => (
                <NavLink key={section.label} to={section.to} end={section.end} className={({ isActive }) => (isActive ? "is-active" : "")}>{section.label}{section.count && section.count(workspace.progress) > 0 && <span className="ws-tab-count">{section.count(workspace.progress)}</span>}</NavLink>
              ))}
            </nav>
            <Outlet context={{ workspace, reload, base, initials }} />
          </>
        )}
      </main>
    </div>
  );
}
