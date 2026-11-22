import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, Check } from "lucide-react";
import { careerDomains } from "../data/careers";
import { apiRequest } from "../services/api";
import ClerkSocialActions from "../components/ClerkSocialActions";
import Brand from "../components/Brand";
import ThemeToggle from "../components/ThemeToggle";
import kenyaAirwaysLogoWhite from "../assets/brand/kenya-airways-logo-white.svg";
import { availabilityOptions, experienceOptions, memberRoles } from "../data/profileOptions";

export default function RegisterPage() {
  const navigate = useNavigate();
  const errorRef = useRef(null);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [role, setRole] = useState("mentee");
  const [domain, setDomain] = useState("");
  const [career, setCareer] = useState("");
  const [experience, setExperience] = useState("");
  const [skills, setSkills] = useState("");
  const [goals, setGoals] = useState("");
  const [availability, setAvailability] = useState("");
  const [registrationError, setRegistrationError] = useState("");

  useEffect(() => {
    if (registrationError) errorRef.current?.scrollIntoView({ block: "center", behavior: "smooth" });
  }, [registrationError]);

  const selectedDomain = careerDomains.find(
    (item) => item.id === domain
  );

  const handleSubmit = async (event) => {
    event.preventDefault();
    setRegistrationError("");

    const registrationData = {
      full_name: fullName,
      email,
      password,
      role,
      profile: {
        career_domain: domain,
        career_path: career,
        experience,
        skills: skills
          .split(",")
          .map((skill) => skill.trim())
          .filter(Boolean),
        certifications: [],
        career_goals: goals,
        mentorship_interests: [],
        availability,
        bio: null,
      },
    };

    try {
      const registered = await apiRequest("/api/auth/register", {
        method: "POST",
        body: JSON.stringify(registrationData),
      });

      navigate("/login", {
        state: registered.verification_email_sent === false
          ? {
              verificationPending: true,
              email,
              notice: "Your account was created. SMTP could not send the verification email, so use the one-time link printed in the backend terminal.",
            }
          : { registered: true, email },
      });
    } catch (error) {
      if (error.message?.toLowerCase().includes("account created, but verification email")) {
        navigate("/login", {
          state: { verificationPending: true, email, notice: error.message },
        });
        return;
      }
      setRegistrationError(error.message || "Registration failed. Check the form and try again.");
    }
  };

  return (
    <main className="register-page">
      <ThemeToggle floating />
      <aside className="register-aside">
        <Brand inverse className="register-brand" />
        <div className="register-aside-body">
          <span className="register-eyebrow">JOIN THE COMMUNITY</span>
          <h1>Tell us where you're headed.</h1>
          <p>
            Your profile helps AlumniConnect identify mentors whose experience,
            competencies and career direction align with yours.
          </p>
          <ul className="register-checklist">
            <li><Check size={14} aria-hidden="true" />Matched by career domain, skills and goals</li>
            <li><Check size={14} aria-hidden="true" />Join as a mentee or as a mentor</li>
            <li><Check size={14} aria-hidden="true" />Update your profile any time</li>
          </ul>
        </div>
        <img className="register-aside-logo" src={kenyaAirwaysLogoWhite} alt="Kenya Airways" />
      </aside>

      <section className="register-main">
        <div className="register-main-inner">
          <Brand className="register-mobile-brand" />
          {import.meta.env.VITE_CLERK_PUBLISHABLE_KEY && <div className="register-social">
            <ClerkSocialActions mode="signup" />
            <p className="register-social-note">
              With Google, Apple or GitHub you choose your role and complete your profile right after signing in.
            </p>
            <p className="auth-divider"><span>OR CREATE AN ACCOUNT WITH EMAIL</span></p>
          </div>}

          <form className="register-form" onSubmit={handleSubmit}>
            <section className="register-section" aria-labelledby="reg-account">
              <header>
                <span>01</span>
                <div>
                  <h2 id="reg-account">Your account</h2>
                  <p>Create your AlumniConnect account.</p>
                </div>
              </header>
              <div className="register-grid">
                <div className="register-field">
                  <label htmlFor="reg-name">Full name</label>
                  <input id="reg-name" type="text" autoComplete="name" value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="e.g. Joy Senetwo" required />
                </div>
                <div className="register-field">
                  <label htmlFor="reg-email">Email address</label>
                  <input id="reg-email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" required />
                </div>
                <div className="register-field register-span">
                  <label htmlFor="reg-password">Password</label>
                  <input id="reg-password" type="password" autoComplete="new-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Create a password" minLength="8" aria-describedby="reg-password-hint" required />
                  <small id="reg-password-hint">Use at least 8 characters.</small>
                </div>
              </div>
            </section>

            <section className="register-section" aria-labelledby="reg-role">
              <header>
                <span>02</span>
                <div>
                  <h2 id="reg-role">Your role</h2>
                  <p>How will you participate in AlumniConnect?</p>
                </div>
              </header>
              <div className="register-roles" role="radiogroup" aria-labelledby="reg-role">
                {memberRoles.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    role="radio"
                    aria-checked={role === item.id}
                    className={`register-role ${role === item.id ? "is-selected" : ""}`}
                    onClick={() => setRole(item.id)}
                  >
                    <span className="register-role-check" aria-hidden="true">{role === item.id && <Check size={14} />}</span>
                    <strong>{item.title}</strong>
                    <span>{item.text}</span>
                  </button>
                ))}
              </div>
            </section>

            <section className="register-section" aria-labelledby="reg-career">
              <header>
                <span>03</span>
                <div>
                  <h2 id="reg-career">Career direction</h2>
                  <p>Tell us which professional path interests you.</p>
                </div>
              </header>
              <div className="register-grid">
                <div className="register-field">
                  <label htmlFor="reg-domain">Career domain</label>
                  <select id="reg-domain" value={domain} onChange={(event) => { setDomain(event.target.value); setCareer(""); }} required>
                    <option value="">Select a career domain</option>
                    {careerDomains.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}
                  </select>
                </div>
                <div className="register-field">
                  <label htmlFor="reg-career-path">Career path</label>
                  <select id="reg-career-path" value={career} onChange={(event) => setCareer(event.target.value)} disabled={!selectedDomain} required>
                    <option value="">{selectedDomain ? "Select a career path" : "Select a domain first"}</option>
                    {selectedDomain?.careers.map((item) => <option value={item} key={item}>{item}</option>)}
                  </select>
                </div>
                <div className="register-field register-span">
                  <label htmlFor="reg-experience">Professional experience</label>
                  <select id="reg-experience" value={experience} onChange={(event) => setExperience(event.target.value)} required>
                    <option value="">Select experience</option>
                    {experienceOptions.map((item) => <option key={item}>{item}</option>)}
                  </select>
                </div>
              </div>
            </section>

            <section className="register-section" aria-labelledby="reg-skills">
              <header>
                <span>04</span>
                <div>
                  <h2 id="reg-skills">Skills &amp; experience</h2>
                  <p>These details will contribute to your semantic profile.</p>
                </div>
              </header>
              <div className="register-field">
                <label htmlFor="reg-skills-input">Skills</label>
                <input id="reg-skills-input" type="text" value={skills} onChange={(event) => setSkills(event.target.value)} placeholder="e.g. Python, Cloud Computing, Leadership, Aircraft Systems" aria-describedby="reg-skills-hint" required />
                <small id="reg-skills-hint">Separate multiple skills with commas.</small>
              </div>
            </section>

            <section className="register-section" aria-labelledby="reg-goals">
              <header>
                <span>05</span>
                <div>
                  <h2 id="reg-goals">Career goals</h2>
                  <p>Describe what you want to achieve professionally.</p>
                </div>
              </header>
              <div className="register-field">
                <label htmlFor="reg-goals-input">What are you hoping to achieve?</label>
                <textarea id="reg-goals-input" value={goals} onChange={(event) => setGoals(event.target.value)} placeholder="Tell us about the career direction, knowledge or experience you are looking for..." rows="5" required />
              </div>
              <div className="register-field">
                <label htmlFor="reg-availability">Mentorship availability</label>
                <select id="reg-availability" value={availability} onChange={(event) => setAvailability(event.target.value)} required>
                  <option value="">Select availability</option>
                  {availabilityOptions.map((item) => <option key={item}>{item}</option>)}
                </select>
              </div>
            </section>

            {registrationError && <p className="auth-error register-error" role="alert" ref={errorRef}>{registrationError}</p>}

            <div className="register-submit">
              <div>
                <strong>Ready to discover your matches?</strong>
                <span>You can update your profile later.</span>
              </div>
              <button type="submit" className="btn btn-primary btn-large">
                Create profile
                <ArrowRight size={17} aria-hidden="true" />
              </button>
            </div>
            <p className="register-signin">
              Already a member? <Link to="/login">Log in</Link>
            </p>
          </form>
        </div>
      </section>
    </main>
  );
}
