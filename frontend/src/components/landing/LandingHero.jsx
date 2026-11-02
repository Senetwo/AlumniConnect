import { Link } from "react-router-dom";
import { ArrowDownRight, ArrowRight, UsersRound } from "lucide-react";
import { getAuth } from "../../services/authStorage";
import aircraftHero from "../../assets/brand/hero-aircraft.webp";

export default function LandingHero() {
  // The hero uses the bundled Kenya Airways aircraft photograph supplied by the
  // project owner. VITE_LANDING_HERO_IMAGE overrides it; see
  // docs/landing-page-visual.md.
  const configuredImage = import.meta.env.VITE_LANDING_HERO_IMAGE?.trim();
  const heroImage = configuredImage || aircraftHero;
  const heroAlt = configuredImage
    ? "Alumni and former colleagues connecting in a professional setting"
    : "A Kenya Airways aircraft flying above the clouds";
  const exploreTarget = getAuth()?.user?.role === "mentee" ? "/mentors" : "/login";

  return (
    <section className="lp-hero" id="home" aria-labelledby="landing-title">
      <img className="lp-hero-image" src={heroImage} alt={heroAlt} fetchpriority="high" />
      <div className="lp-hero-shade" aria-hidden="true" />

      <div className="lp-hero-inner">
        <div className="lp-hero-copy">
          <span className="lp-eyebrow">ALUMNI &amp; FORMER COLLEAGUES</span>
          <h1 id="landing-title">
            Your journey doesn’t end <span>when the chapter changes.</span>
          </h1>
          <p>
            Stay connected to your community through mentorship, shared knowledge
            and meaningful relationships.
          </p>
          <div className="lp-hero-actions">
            <Link to="/register" className="lp-btn lp-btn-primary">
              Join the community <ArrowRight size={17} aria-hidden="true" />
            </Link>
            <Link to={exploreTarget} className="lp-btn lp-btn-ghost">
              Explore mentorship <ArrowDownRight size={17} aria-hidden="true" />
            </Link>
          </div>
          <div className="lp-hero-note">
            <UsersRound size={17} aria-hidden="true" />
            <span>For alumni, mentors and the next generation of talent</span>
          </div>
        </div>
      </div>
    </section>
  );
}
