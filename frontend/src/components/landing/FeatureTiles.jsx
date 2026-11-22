import { Link } from "react-router-dom";
import { ArrowRight, BriefcaseBusiness, Compass, Heart, UsersRound } from "lucide-react";
import { getAuth } from "../../services/authStorage";

// The project's three purposes. Wording describes what the app does today:
// mentorship, the Knowledge Hub and the member directory.
const purposes = [
  {
    number: "01",
    icon: UsersRound,
    title: "Network & Connect",
    text: "Build meaningful relationships with fellow alumni.",
    status: "Explore the directory",
    href: "/directory",
  },
  {
    number: "02",
    icon: BriefcaseBusiness,
    title: "Career Growth",
    text: "Access mentorship and learning resources.",
    status: "Explore mentorship",
    href: "/mentors",
  },
  {
    number: "03",
    icon: Heart,
    title: "Give Back",
    text: "Contribute by mentoring fellow alumni.",
    status: "Become a mentor",
    href: "/register",
  },
];

// The three purposes in one panel that overlaps the hero's lower edge.
export default function FeatureTiles() {
  const signedIn = Boolean(getAuth());

  return (
    <section className="lp-panel-wrap" id="features" aria-labelledby="features-title">
      <div className="lp-panel">
        <div className="lp-panel-head">
          <div>
            <span className="lp-eyebrow lp-eyebrow-red">A COMMUNITY WITH PURPOSE</span>
            <h2 id="features-title">Make the most of every connection.</h2>
          </div>
          <p>Start with the tools available today, and help shape a stronger alumni community for tomorrow.</p>
        </div>

        <div className="lp-tiles">
          {purposes.map(({ number, icon: Icon, title, text, status, href }) => (
            <article className="lp-tile" key={number}>
              <div className="lp-tile-top">
                <span>{number}</span>
                <span className="lp-tile-icon" aria-hidden="true"><Icon size={22} /></span>
              </div>
              <h3>{title}</h3>
              <p>{text}</p>
              <Link
                to={href === "/directory" && !signedIn ? "/login" : href}
                className="lp-tile-link"
              >
                {status}
                <ArrowRight size={15} aria-hidden="true" />
              </Link>
            </article>
          ))}
        </div>

        <div className="lp-engaged">
          <span className="lp-engaged-icon" aria-hidden="true"><Compass size={20} /></span>
          <div>
            <strong>Stay engaged with your community</strong>
            <p>
              Keep up with relevant mentorship activity. Organization-wide news and alumni
              announcements are part of the platform vision.
            </p>
          </div>
          <Link to="/login" className="lp-text-link">
            Sign in to continue <ArrowRight size={15} aria-hidden="true" />
          </Link>
        </div>
      </div>
    </section>
  );
}
