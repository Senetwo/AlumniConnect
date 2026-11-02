import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import Feed from "../components/community/Feed";
import MemberDirectory from "../components/community/MemberDirectory";
import { EventsCard, JobsCard } from "../components/community/SidePanels";
import { careerDomains } from "../data/careers";
import { apiRequest } from "../services/api";
import { getAuth } from "../services/authStorage";
import { initials } from "../utils/format";

const domainLabel = (value) => careerDomains.find((domain) => domain.id === value)?.name || value;

const tabs = [
  { id: "feed", label: "Community feed" },
  { id: "members", label: "Members" },
];

export default function DirectoryPage() {
  const me = getAuth()?.user;
  const [tab, setTab] = useState("feed");
  const [profile, setProfile] = useState(null);
  const [pending, setPending] = useState(0);
  const [connected, setConnected] = useState(0);

  useEffect(() => {
    let active = true;
    apiRequest("/api/profiles/me").then((data) => { if (active) setProfile(data); }).catch(() => {});
    apiRequest("/api/connections").then((items) => {
      if (!active) return;
      setConnected(items.filter((item) => item.status === "accepted").length);
      setPending(items.filter((item) => item.status === "pending" && item.recipient_id === me?.id).length);
    }).catch(() => {});
    return () => { active = false; };
  }, [me?.id]);

  return <div className="app"><Navbar /><main className="cm-page">
    <aside className="cm-left" aria-label="Your profile">
      <section className="cm-card cm-me">
        <div className="cm-me-cover" aria-hidden="true" />
        <div className="cm-avatar cm-avatar-lg" aria-hidden="true">
          {profile?.profile_picture_url ? <img src={profile.profile_picture_url} alt="" /> : initials(me?.full_name)}
        </div>
        <h2>{me?.full_name}</h2>
        <p className="cm-me-role">{me?.community_role || me?.role}{profile?.career_path ? ` · ${profile.career_path}` : ""}</p>
        {profile && <p className="cm-meta">{domainLabel(profile.career_domain)}</p>}
        <dl className="cm-me-stats">
          <div><dt>Directory</dt><dd>{profile ? (profile.directory_visible ? "Visible" : "Hidden") : "…"}</dd></div>
          <div><dt>Connections</dt><dd>{connected}</dd></div>
          <div><dt>Requests</dt><dd>{pending}</dd></div>
        </dl>
        <Link to="/profile" className="btn btn-outline cm-small">Edit profile</Link>
      </section>
    </aside>

    <section className="cm-center">
      <div className="cm-tabs" role="tablist" aria-label="Community sections">
        {tabs.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            id={`cm-tab-${item.id}`}
            aria-selected={tab === item.id}
            aria-controls={`cm-panel-${item.id}`}
            className={tab === item.id ? "is-active" : ""}
            onClick={() => setTab(item.id)}
          >
            {item.label}{item.id === "members" && pending > 0 && <span className="cm-badge">{pending}</span>}
          </button>
        ))}
      </div>
      <div role="tabpanel" id="cm-panel-feed" aria-labelledby="cm-tab-feed" hidden={tab !== "feed"}>{tab === "feed" && <Feed me={me} />}</div>
      <div role="tabpanel" id="cm-panel-members" aria-labelledby="cm-tab-members" hidden={tab !== "members"}>{tab === "members" && <MemberDirectory me={me} onPendingChange={setPending} />}</div>
    </section>

    <aside className="cm-right" aria-label="Events and opportunities">
      <EventsCard />
      <JobsCard />
    </aside>
  </main></div>;
}
