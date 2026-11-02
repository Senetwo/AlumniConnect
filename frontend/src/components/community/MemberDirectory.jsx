import { useCallback, useEffect, useState } from "react";
import { Check, Search, UserPlus, UserRound } from "lucide-react";
import { careerDomains } from "../../data/careers";
import { apiRequest } from "../../services/api";
import { initials } from "../../utils/format";

// Older profiles store the domain id (e.g. "technology-digital"); show its name.
const domainLabel = (value) => careerDomains.find((domain) => domain.id === value)?.name || value;

export default function MemberDirectory({ me, onPendingChange }) {
  const [members, setMembers] = useState([]);
  const [connections, setConnections] = useState([]);
  const [career, setCareer] = useState("");
  const [skill, setSkill] = useState("");
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    setError("");
    try {
      const params = new URLSearchParams();
      if (career.trim()) params.set("career_domain", career.trim());
      if (skill.trim()) params.set("skill", skill.trim());
      const directory = await apiRequest(`/api/directory?${params}`);
      setMembers(directory.items || []);
      setConnections(directory.connections || []);
      onPendingChange?.((directory.connections || []).filter((item) => item.status === "pending" && item.recipient_id === me?.id).length);
    } catch (err) {
      setError(err instanceof TypeError
        ? "Could not reach the directory API. Make sure the backend is running, then refresh the page."
        : err.message || "Unable to load the directory.");
    }
  }, [career, skill, me?.id, onPendingChange]);

  useEffect(() => { queueMicrotask(() => { void load(); }); }, [load]);

  async function connect(memberId) {
    setBusyId(memberId);
    try {
      await apiRequest("/api/connections", { method: "POST", body: JSON.stringify({ user_id: memberId }) });
      await load();
    } catch (err) { setError(err.message || "Could not send connection request."); }
    finally { setBusyId(null); }
  }

  async function respond(connectionId, action) {
    try {
      await apiRequest(`/api/connections/${connectionId}/${action}`, { method: "PATCH" });
      await load();
    } catch (err) { setError(err.message || "Could not update connection request."); }
  }

  async function moderate(memberId, mode) {
    if (mode === "block" && !window.confirm("Block this member? They will disappear from your directory and messaging will stop.")) return;
    if (mode === "report") {
      const reason = window.prompt("Why are you reporting this member? (e.g. harassment, spam, impersonation)");
      if (!reason?.trim()) return;
      try { await apiRequest("/api/members/report", { method: "POST", body: JSON.stringify({ user_id: memberId, reason: reason.trim() }) }); setError("Report sent to the moderation team."); }
      catch (err) { setError(err.message || "Unable to submit report."); }
      return;
    }
    try { await apiRequest(`/api/members/${memberId}/block`, { method: "POST" }); await load(); }
    catch (err) { setError(err.message || "Unable to block member."); }
  }

  const existing = (id) => connections.find((connection) => connection.other_user?.id === id);
  const incoming = connections.filter((item) => item.status === "pending" && item.recipient_id === me?.id);

  return (
    <div className="cm-members">
      <div className="cm-card cm-filters">
        <label><Search size={17} aria-hidden="true" /><span className="visually-hidden">Filter by career area</span><input value={career} onChange={(event) => setCareer(event.target.value)} placeholder="Career area" /></label>
        <label><Search size={17} aria-hidden="true" /><span className="visually-hidden">Filter by skill</span><input value={skill} onChange={(event) => setSkill(event.target.value)} placeholder="Skill" /></label>
      </div>

      {error && <div role="alert" className="page-alert">{error}</div>}

      {incoming.length > 0 && (
        <section className="cm-card cm-requests" aria-label="Connection requests">
          <h2>Connection requests</h2>
          {incoming.map((item) => (
            <div key={item.id} className="cm-request">
              <span><strong>{item.other_user?.full_name}</strong> would like to connect</span>
              <button className="btn btn-primary cm-small" onClick={() => respond(item.id, "accept")}>Accept</button>
              <button className="btn btn-outline cm-small" onClick={() => respond(item.id, "decline")}>Decline</button>
            </div>
          ))}
        </section>
      )}

      {members.length === 0 && !error ? (
        <div className="cm-card cm-empty">
          <UserRound size={28} aria-hidden="true" />
          <h2>No visible members found</h2>
          <p>Try another search, or check back as members opt in.</p>
        </div>
      ) : members.map((member) => {
        const connection = existing(member.user_id);
        return (
          <article className="cm-card cm-member" key={member.user_id}>
            <div className="cm-avatar" aria-hidden="true">
              {member.profile_picture_url ? <img src={member.profile_picture_url} alt="" /> : initials(member.full_name)}
            </div>
            <div className="cm-member-body">
              <h2>{member.full_name}</h2>
              <p className="cm-member-role">{member.role} · {domainLabel(member.career_domain)} · {member.career_path}</p>
              <p className="cm-meta">{member.experience}</p>
              {member.bio && <p className="cm-member-bio">{member.bio}</p>}
              <div className="cm-chips">{member.skills.slice(0, 5).map((item) => <span key={item}>{item}</span>)}</div>
            </div>
            <div className="cm-member-actions">
              {!connection ? (
                <button className="btn btn-outline cm-small" disabled={busyId === member.user_id} onClick={() => connect(member.user_id)}>
                  <UserPlus size={15} aria-hidden="true" />{busyId === member.user_id ? "Sending…" : "Connect"}
                </button>
              ) : (
                <span className="cm-status"><Check size={15} aria-hidden="true" />{connection.status === "accepted" ? "Connected" : connection.status === "pending" ? (connection.requester_id === member.user_id ? "Request received" : "Request sent") : connection.status}</span>
              )}
              <div className="cm-quiet">
                <button type="button" onClick={() => moderate(member.user_id, "report")}>Report</button>
                <button type="button" onClick={() => moderate(member.user_id, "block")}>Block</button>
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}
