import { useState } from "react";
import { useAuth, useUser } from "@clerk/react";
import { useNavigate } from "react-router-dom";
import { Check } from "lucide-react";
import Brand from "../components/Brand";
import OtpStep from "../components/OtpStep";
import { careerDomains } from "../data/careers";
import { availabilityOptions, experienceOptions, memberRoles } from "../data/profileOptions";
import { apiRequest } from "../services/api";
import { saveClerkAuth } from "../services/authStorage";

const initial = {
  role: "mentee",
  career_domain: "",
  career_path: "",
  experience: "",
  skills: "",
  career_goals: "",
  availability: "",
};

export default function ClerkOnboardingPage() {
  const { isLoaded, user } = useUser();
  const { getToken } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [linkMode, setLinkMode] = useState(false);
  const [legacyEmail, setLegacyEmail] = useState("");
  const [legacyPassword, setLegacyPassword] = useState("");
  const [linkChallenge, setLinkChallenge] = useState(null);

  const selectedDomain = careerDomains.find((item) => item.id === form.career_domain);
  const update = (event) => setForm((current) => ({
    ...current,
    [event.target.name]: event.target.value,
    ...(event.target.name === "career_domain" ? { career_path: "" } : {}),
  }));
  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const token = await getToken();
      const profile = {
        career_domain: form.career_domain.trim(),
        career_path: form.career_path.trim(),
        experience: form.experience.trim(),
        skills: form.skills.split(",").map((item) => item.trim()).filter(Boolean),
        certifications: [],
        career_goals: form.career_goals.trim(),
        mentorship_interests: [],
        availability: form.availability.trim(),
      };
      const account = await apiRequest("/api/auth/clerk/onboard", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          full_name: user?.fullName || user?.primaryEmailAddress?.emailAddress?.split("@")[0] || "Alumni member",
          role: form.role,
          profile,
        }),
      });
      saveClerkAuth(token, account);
      navigate(form.role === "mentor" ? "/mentor-workspace" : "/mentors", { replace: true });
    } catch (submissionError) {
      setError(submissionError.message || "Unable to complete account setup.");
    } finally {
      setBusy(false);
    }
  };

  const finishLink = async (legacyToken) => {
    const clerkToken = await getToken();
    const account = await apiRequest("/api/auth/clerk/link", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${legacyToken}`,
        "X-Clerk-Authorization": `Bearer ${clerkToken}`,
      },
    });
    saveClerkAuth(clerkToken, account);
    navigate(account.role === "admin" ? "/admin" : account.role === "mentor" ? "/mentor-workspace" : "/mentors", { replace: true });
  };

  const linkExistingAccount = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const legacySession = await apiRequest("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: legacyEmail, password: legacyPassword }),
        headers: {},
      });
      if (legacySession.mfa_required) {
        setLinkChallenge(legacySession);
        setLegacyPassword("");
        return;
      }
      await finishLink(legacySession.access_token);
    } catch (linkError) {
      setError(linkError.message || "Unable to link these accounts.");
    } finally {
      setBusy(false);
    }
  };

  if (!isLoaded) return <main className="register-solo"><p role="status">Loading your account…</p></main>;

  return <main className="register-page register-solo">
    <div className="register-main-inner">
      <Brand className="register-solo-brand" />
      <div className="register-solo-heading">
        <span className="register-eyebrow register-eyebrow-light">WELCOME TO ALUMNICONNECT</span>
        <h1 id="onboarding-title">Set up your community profile</h1>
        <p>Choose a member role and add the career information used for mentoring and discovery.</p>
      </div>

      <form className="register-form" onSubmit={submit} aria-labelledby="onboarding-title">
        <section className="register-section" aria-labelledby="ob-role">
          <header><span>01</span><div><h2 id="ob-role">Your role</h2><p>How will you participate in AlumniConnect?</p></div></header>
          <div className="register-roles" role="radiogroup" aria-labelledby="ob-role">
            {memberRoles.map((item) => <button
              key={item.id}
              type="button"
              role="radio"
              aria-checked={form.role === item.id}
              className={`register-role ${form.role === item.id ? "is-selected" : ""}`}
              onClick={() => setForm((current) => ({ ...current, role: item.id }))}
            >
              <span className="register-role-check" aria-hidden="true">{form.role === item.id && <Check size={14} />}</span>
              <strong>{item.title}</strong>
              <span>{item.text}</span>
            </button>)}
          </div>
        </section>

        <section className="register-section" aria-labelledby="ob-career">
          <header><span>02</span><div><h2 id="ob-career">Career direction</h2><p>Tell us which professional path interests you.</p></div></header>
          <div className="register-grid">
            <div className="register-field">
              <label htmlFor="clerk-career_domain">Career domain</label>
              <select id="clerk-career_domain" name="career_domain" value={form.career_domain} onChange={update} required>
                <option value="">Select a career domain</option>
                {careerDomains.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}
              </select>
            </div>
            <div className="register-field">
              <label htmlFor="clerk-career_path">Career path</label>
              <select id="clerk-career_path" name="career_path" value={form.career_path} onChange={update} disabled={!selectedDomain} required>
                <option value="">{selectedDomain ? "Select a career path" : "Select a domain first"}</option>
                {selectedDomain?.careers.map((item) => <option value={item} key={item}>{item}</option>)}
              </select>
            </div>
            <div className="register-field register-span">
              <label htmlFor="clerk-experience">Professional experience</label>
              <select id="clerk-experience" name="experience" value={form.experience} onChange={update} required>
                <option value="">Select experience</option>
                {experienceOptions.map((item) => <option key={item}>{item}</option>)}
              </select>
            </div>
          </div>
        </section>

        <section className="register-section" aria-labelledby="ob-goals">
          <header><span>03</span><div><h2 id="ob-goals">Skills and goals</h2><p>These details contribute to your semantic profile.</p></div></header>
          <div className="register-field">
            <label htmlFor="clerk-skills">Skills</label>
            <input id="clerk-skills" name="skills" value={form.skills} onChange={update} placeholder="e.g. Python, Leadership, Aircraft Systems" maxLength={500} aria-describedby="clerk-skills-hint" required />
            <small id="clerk-skills-hint">Separate multiple skills with commas.</small>
          </div>
          <div className="register-field">
            <label htmlFor="clerk-career_goals">What are you hoping to achieve?</label>
            <textarea id="clerk-career_goals" name="career_goals" value={form.career_goals} onChange={update} rows="4" maxLength={500} required />
          </div>
          <div className="register-field">
            <label htmlFor="clerk-availability">Mentorship availability</label>
            <select id="clerk-availability" name="availability" value={form.availability} onChange={update} required>
              <option value="">Select availability</option>
              {availabilityOptions.map((item) => <option key={item}>{item}</option>)}
            </select>
          </div>
        </section>

        {error && <p className="auth-error register-error" role="alert">{error}</p>}
        <div className="register-submit">
          <div><strong>Almost there</strong><span>You can update your profile later.</span></div>
          <button className="btn btn-primary btn-large" type="submit" disabled={busy}>{busy ? "Saving profile…" : "Complete account setup"}</button>
        </div>
      </form>

      <section className="register-section register-link-panel">
        <button type="button" className="auth-text-button" onClick={() => { setLinkMode((value) => !value); setError(""); }}>
          {linkMode ? "Create a new AlumniConnect profile instead" : "Already have an AlumniConnect account? Link it"}
        </button>
        {linkMode && linkChallenge && <OtpStep challenge={linkChallenge} onVerified={finishLink} onCancel={() => setLinkChallenge(null)} />}
        {linkMode && !linkChallenge && <form onSubmit={linkExistingAccount} className="register-form">
          <div className="register-field"><label htmlFor="legacy-email">Existing account email</label><input id="legacy-email" type="email" value={legacyEmail} onChange={(event) => setLegacyEmail(event.target.value)} required autoComplete="username" /></div>
          <div className="register-field"><label htmlFor="legacy-password">Existing account password</label><input id="legacy-password" type="password" value={legacyPassword} onChange={(event) => setLegacyPassword(event.target.value)} required autoComplete="current-password" /></div>
          <button className="btn btn-outline" type="submit" disabled={busy}>{busy ? "Linking…" : "Verify both accounts and link"}</button>
        </form>}
      </section>
      <p className="register-legal">Administrator access is assigned separately by AlumniConnect administrators.</p>
    </div>
  </main>;
}
