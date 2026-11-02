import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Search, SlidersHorizontal, UserRound } from "lucide-react";
import Navbar from "../components/Navbar";
import MatchBadge from "../components/MatchBadge";
import RequestMentorship, { RequestStatusChip } from "../components/RequestMentorship";
import useMentorshipStatuses from "../hooks/useMentorshipStatuses";
import { careerDomains } from "../data/careers";
import { apiRequest } from "../services/api";
import { getAuth } from "../services/authStorage";
import { matchLabels } from "../utils/matching";

// Older profiles store the domain id (e.g. "technology-digital"); show its name.
const domainLabel = (value) => careerDomains.find((domain) => domain.id === value)?.name || value;

function getSkills(mentor) {
  return (mentor.skills || []).map((skill) => skill.trim()).filter(Boolean);
}

export default function MentorsPage() {
  const [mentors, setMentors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedDomain, setSelectedDomain] = useState("");
  const [selectedCompetency, setSelectedCompetency] = useState("");
  const { byMentor, reload } = useMentorshipStatuses();

  useEffect(() => {
    let active = true;

    async function loadMentors() {
      if (!getAuth()) {
        window.location.href = "/login";
        return;
      }

      try {
        const data = await apiRequest("/api/matches/me");
        if (active) setMentors(data.matches || []);
      } catch (requestError) {
        if (active) {
          setError(requestError.message || "Unable to load mentor recommendations.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    loadMentors();
    return () => { active = false; };
  }, [loadAttempt]);

  const matches = matchLabels(mentors);
  const availableDomains = [...new Set(mentors.map((mentor) => mentor.career_domain).filter(Boolean))].sort();
  const availableCompetencies = [...new Set(mentors.flatMap(getSkills))].sort();
  const query = searchTerm.trim().toLowerCase();
  const filteredMentors = mentors.filter((mentor) => {
    const searchableText = [
      mentor.full_name,
      mentor.career_path,
      mentor.career_domain,
      mentor.experience,
      mentor.bio,
      ...getSkills(mentor),
    ].filter(Boolean).join(" ").toLowerCase();

    return (!query || searchableText.includes(query)) &&
      (!selectedDomain || mentor.career_domain === selectedDomain) &&
      (!selectedCompetency || getSkills(mentor).includes(selectedCompetency));
  });

  function clearFilters() {
    setSearchTerm("");
    setSelectedDomain("");
    setSelectedCompetency("");
  }

  return (
    <div className="app">
      <Navbar />
      <main className="mentors-page">
        <header className="mentors-header">
          <div>
            <span className="eyebrow">MENTOR DISCOVERY</span>
            <h1>Recommended mentors</h1>
            <p>Explore professional experience aligned with your career profile and goals.</p>
          </div>
        </header>

        <section className="mentor-filters" aria-label="Filter mentors">
          <label className="search-box">
            <Search size={17} aria-hidden="true" />
            <input
              type="search"
              placeholder="Search by name, skill, or experience"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              aria-label="Search mentors"
            />
          </label>
          <select value={selectedDomain} onChange={(event) => setSelectedDomain(event.target.value)} aria-label="Filter by professional area">
            <option value="">All professional areas</option>
            {availableDomains.map((domain) => <option key={domain} value={domain}>{domainLabel(domain)}</option>)}
          </select>
          <select value={selectedCompetency} onChange={(event) => setSelectedCompetency(event.target.value)} aria-label="Filter by skill">
            <option value="">All skills</option>
            {availableCompetencies.map((skill) => <option key={skill} value={skill}>{skill}</option>)}
          </select>
          <button type="button" className="filter-button" onClick={clearFilters}>
            <SlidersHorizontal size={16} aria-hidden="true" /> Clear filters
          </button>
        </section>

        {loading ? (
          <div className="mentor-results" role="status" aria-label="Loading mentor recommendations">
            {[1, 2, 3].map((item) => <div className="mentor-result-skeleton" key={item} />)}
          </div>
        ) : error ? (
          <section className="mentor-state-card" role="alert">
            <h2>We couldn’t load recommendations</h2>
            <p>{error}</p>
            <button type="button" className="btn btn-primary" onClick={() => {
              setLoading(true);
              setLoadAttempt((attempt) => attempt + 1);
            }}>
              Try again
            </button>
          </section>
        ) : filteredMentors.length === 0 ? (
          <section className="mentor-state-card">
            <h2>{mentors.length ? "No mentors match those filters" : "No recommendations yet"}</h2>
            <p>{mentors.length ? "Try a different search or clear your filters." : "Complete your profile with your experience and career goals to help us find relevant mentors."}</p>
            {mentors.length ? (
              <button type="button" className="btn btn-outline" onClick={clearFilters}>Clear filters</button>
            ) : (
              <Link to="/profile" className="btn btn-primary">Update my profile</Link>
            )}
          </section>
        ) : (
          <section className="mentor-results" aria-label="Mentor recommendations">
            {filteredMentors.map((mentor) => {
              const skills = getSkills(mentor);
              const record = byMentor[mentor.user_id];

              return (
                <article className="mentor-result-card" key={mentor.id}>
                  <div className="mentor-card-header">
                    <div className="mentor-identity">
                      <div className="mentor-avatar large">
                        {mentor.profile_picture_url ? (
                          <img
                            src={mentor.profile_picture_url}
                            alt=""
                            className="mentor-profile-image"
                            onError={(event) => {
                              event.currentTarget.style.display = "none";
                              event.currentTarget.nextElementSibling.style.display = "flex";
                            }}
                          />
                        ) : null}
                        <span className="mentor-avatar-fallback" style={{ display: mentor.profile_picture_url ? "none" : "flex" }} aria-hidden="true">
                          {mentor.full_name?.split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase() || <UserRound size={19} />}
                        </span>
                      </div>
                      <div>
                        <h2>{mentor.full_name || mentor.career_path || "Alumni mentor"}</h2>
                        <p>{mentor.career_path}</p>
                      </div>
                    </div>
                    <div className="mentor-card-badges">
                      <MatchBadge match={matches[mentor.id]} />
                      <RequestStatusChip record={record} />
                    </div>
                  </div>

                  <div className="mentor-meta">
                    {mentor.career_domain && <span>{domainLabel(mentor.career_domain)}</span>}
                    {mentor.experience && <span>{mentor.experience}</span>}
                    {mentor.availability && <span>Available: {mentor.availability}</span>}
                  </div>

                  {skills.length > 0 && (
                    <div className="competencies" aria-label="Areas of expertise">
                      {skills.slice(0, 3).map((skill) => <span key={skill}>{skill}</span>)}
                      {skills.length > 3 && <Link to={`/mentor-profile/${mentor.id}`} className="more-skills-link">+{skills.length - 3} more</Link>}
                    </div>
                  )}

                  <div className="mentor-card-actions">
                    <Link to={`/mentor-profile/${mentor.id}`} className="btn btn-outline">View profile</Link>
                    <RequestMentorship mentor={mentor} record={record} onChanged={reload} />
                  </div>
                </article>
              );
            })}
          </section>
        )}
      </main>
    </div>
  );
}
