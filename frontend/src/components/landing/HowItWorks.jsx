const steps = [
  ["01", "Join the community", "Create an account as a mentee or mentor."],
  ["02", "Share your experience", "Build a profile with your skills, background and goals."],
  ["03", "Explore mentorship", "Discover relevant mentors and request a connection."],
  ["04", "Keep learning", "Use the Knowledge Hub and continue your journey."],
];

export default function HowItWorks() {
  return (
    <section className="lp-band" id="how-it-works" aria-labelledby="journey-title">
      <div className="lp-band-inner">
        <div className="lp-band-head">
          <div>
            <span className="lp-eyebrow">YOUR NEXT CHAPTER</span>
            <h2 id="journey-title">A simple place to begin.</h2>
          </div>
          <p>Whether you’re ready to learn or ready to share, your journey starts with a profile.</p>
        </div>

        <ol className="lp-steps">
          {steps.map(([number, title, text]) => (
            <li key={number}>
              <span className="lp-step-number">{number}</span>
              <h3>{title}</h3>
              <p>{text}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
