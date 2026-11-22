import { Link } from "react-router-dom";
import { ArrowRight, UsersRound } from "lucide-react";
import Navbar from "../components/Navbar";
import LandingHero from "../components/landing/LandingHero";
import FeatureTiles from "../components/landing/FeatureTiles";
import HowItWorks from "../components/landing/HowItWorks";
import KnowledgePreview from "../components/landing/KnowledgePreview";

function PurposeSection() {
  return (
    <section className="lp-section" id="about" aria-labelledby="purpose-title">
      <div className="lp-kicker"><span>WHY ALUMNICONNECT</span></div>
      <div className="lp-purpose">
        <h2 id="purpose-title">A career community is strongest when it stays connected.</h2>
        <div>
          <p>
            The relationships built through work and shared experience can
            continue to create value long after a role or graduation ends.
            AlumniConnect brings mentorship and useful knowledge into one
            place, making it easier to give back and keep moving forward.
          </p>
          <a className="lp-text-link" href="#features">Discover what you can do <ArrowRight size={16} aria-hidden="true" /></a>
        </div>
      </div>
    </section>
  );
}

function ClosingCta() {
  return (
    <section className="lp-cta" aria-labelledby="cta-title">
      <div className="lp-cta-inner">
        <span className="lp-cta-symbol" aria-hidden="true"><UsersRound size={25} /></span>
        <span className="lp-eyebrow">YOUR COMMUNITY IS HERE</span>
        <h2 id="cta-title">Stay connected.<br />Keep growing. Give back.</h2>
        <p>Bring your experience and your ambition. There’s room for both.</p>
        <Link to="/register" className="lp-btn lp-btn-light">
          Join the community <ArrowRight size={17} aria-hidden="true" />
        </Link>
      </div>
    </section>
  );
}

function LandingPage() {
  return (
    <div className="app landing-page">
      <Navbar landing />
      <main>
        <LandingHero />
        <FeatureTiles />
        <PurposeSection />
        <HowItWorks />
        <KnowledgePreview />
        <ClosingCta />
      </main>
    </div>
  );
}

export default LandingPage;
