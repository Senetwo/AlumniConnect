import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Briefcase, Clock, GraduationCap } from "lucide-react";
import Navbar from "../components/Navbar";
import MatchBadge from "../components/MatchBadge";
import RequestMentorship, { RequestStatusChip } from "../components/RequestMentorship";
import useMentorshipStatuses from "../hooks/useMentorshipStatuses";
import { careerDomains } from "../data/careers";
import { apiRequest } from "../services/api";
import { initials } from "../utils/format";
import { matchLabels } from "../utils/matching";

const domainLabel = (value) => careerDomains.find((domain) => domain.id === value)?.name || value;

export default function MentorProfilePage() {
  const { mentorId } = useParams();
  const [mentors, setMentors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const { byMentor, reload } = useMentorshipStatuses();

  useEffect(() => {
    async function loadMentor() {
      try {
        // Load the signed-in mentee's matches and find the selected mentor.
        const data = await apiRequest("/api/matches/me");
        setMentors(data.matches || []);
      } catch (err) {
        setError(err.message || "Could not load this mentor.");
      } finally {
        setLoading(false);
      }
    }

    loadMentor();
  }, []);

  const mentor = mentors.find((item) => String(item.id) === String(mentorId));
  const record = mentor ? byMentor[mentor.user_id] : null;
  const match = mentor ? matchLabels(mentors)[mentor.id] : null;

  return (
    <div className="app">
      <Navbar />

      <main className="mp-page">
        <Link to="/mentors" className="mp-back"><ArrowLeft size={16} aria-hidden="true" />Back to recommended mentors</Link>

        {loading ? (
          <div className="mp-card mp-skeleton" role="status" aria-label="Loading mentor profile" />
        ) : error || !mentor ? (
          <section className="mp-card mp-empty" role="alert">
            <h1>Mentor profile unavailable</h1>
            <p>{error || "This mentor was not found in your recommendations."}</p>
            <Link to="/mentors" className="btn btn-primary">Back to mentors</Link>
          </section>
        ) : (
          <div className="mp-layout">
            <div className="mp-main">
              <section className="mp-card mp-hero">
                <div className="mp-cover" aria-hidden="true" />
                <div className="mp-avatar" aria-hidden="true">
                  {mentor.profile_picture_url ? <img src={mentor.profile_picture_url} alt="" /> : initials(mentor.full_name)}
                </div>
                <div className="mp-hero-body">
                  <div className="mp-hero-title">
                    <div>
                      <h1>{mentor.full_name || mentor.career_path}</h1>
                      <p>{mentor.career_path}</p>
                    </div>
                    <div className="mentor-card-badges">
                      <MatchBadge match={match} />
                      <RequestStatusChip record={record} />
                    </div>
                  </div>
                  <ul className="mp-facts">
                    <li><Briefcase size={16} aria-hidden="true" />{domainLabel(mentor.career_domain)}</li>
                    {mentor.experience && <li><GraduationCap size={16} aria-hidden="true" />{mentor.experience}</li>}
                    {mentor.availability && <li><Clock size={16} aria-hidden="true" />Available: {mentor.availability}</li>}
                  </ul>
                </div>
              </section>

              <section className="mp-card" aria-labelledby="mp-about">
                <h2 id="mp-about">About</h2>
                <p>{mentor.bio || "This mentor hasn't added a bio yet."}</p>
              </section>

              <section className="mp-card" aria-labelledby="mp-skills">
                <h2 id="mp-skills">Skills and competencies</h2>
                {mentor.skills?.length ? (
                  <div className="competencies">
                    {mentor.skills.map((skill) => <span key={skill}>{skill}</span>)}
                  </div>
                ) : (
                  <p>No skills listed yet.</p>
                )}
              </section>
            </div>

            <aside className="mp-aside">
              <section className="mp-card mp-request" aria-labelledby="mp-request-title">
                <h2 id="mp-request-title">Work with {mentor.full_name?.split(" ")[0] || "this mentor"}</h2>
                <p className="mp-note">
                  Ranked by how closely their experience, skills and goals fit your profile. It is a guide, not a prediction of how the mentorship will go.
                </p>
                <RequestMentorship mentor={mentor} record={record} onChanged={reload} />
              </section>
            </aside>
          </div>
        )}
      </main>
    </div>
  );
}
