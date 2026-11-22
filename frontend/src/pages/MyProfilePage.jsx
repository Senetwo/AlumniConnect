import { useEffect, useState } from "react";
import { Camera, Check, Circle, Save } from "lucide-react";
import Navbar from "../components/Navbar";
import { careerDomains } from "../data/careers";
import { availabilityOptions, experienceOptions } from "../data/profileOptions";
import { getAuth } from "../services/authStorage";
import { displayEmail, initials } from "../utils/format";

// Keep a stored value selectable even when it is not in the current option list
// (older profiles used free text).
const domainName = (value) => careerDomains.find((domain) => domain.id === value)?.name || value || "";
const withCurrent = (options, current) => (current && !options.includes(current) ? [current, ...options] : options);

export default function MyProfilePage() {
  const [, setProfile] = useState(null);
  const [form, setForm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [photoFile, setPhotoFile] = useState(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [snapshot, setSnapshot] = useState(null);
  const token = getAuth()?.token;
  const account = getAuth()?.user;

  useEffect(() => {
    async function loadProfile() {
      try {
        const response = await fetch("http://127.0.0.1:8000/api/profiles/me", {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || "Could not load profile.");
        }

        const data = await response.json();
        setProfile(data);
        setForm({
          career_domain: careerDomains.find((domain) => domain.id === data.career_domain || domain.name === data.career_domain)?.id || data.career_domain || "",
          career_path: data.career_path || "",
          experience: data.experience || "",
          skills: (data.skills || []).join(", "),
          certifications: (data.certifications || []).join(", "),
          career_goals: data.career_goals || "",
          mentorship_interests: (data.mentorship_interests || []).join(", "),
          availability: data.availability || "",
          bio: data.bio || "",
          profile_picture_url: data.profile_picture_url || "",
          directory_visible: Boolean(data.directory_visible),
        });
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadProfile();
  }, [token]);

  useEffect(() => {
    if (form && snapshot === null) queueMicrotask(() => setSnapshot(JSON.stringify(form)));
  }, [form, snapshot]);

  const dirty = Boolean(form && snapshot && JSON.stringify(form) !== snapshot);

  useEffect(() => {
    if (!dirty) return undefined;
    const warn = (event) => { event.preventDefault(); event.returnValue = ""; };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  const handleChange = (event) => {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
    setMessage("");
  };

  const handlePhotoUpload = async (event) => {
    event.preventDefault();
    if (!photoFile) {
      setError("Choose an image first.");
      return;
    }

    setUploadingPhoto(true);
    setError("");
    setMessage("");

    try {
      const uploadData = new FormData();
      uploadData.append("file", photoFile);
      const response = await fetch("http://127.0.0.1:8000/api/profiles/me/photo", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: uploadData,
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Could not upload profile photo."
        );
      }

      setForm((current) => ({ ...current, profile_picture_url: data.profile_picture_url }));
      setSnapshot((current) => (current ? JSON.stringify({ ...JSON.parse(current), profile_picture_url: data.profile_picture_url }) : current));
      setPhotoFile(null);
      event.target.reset();
      setMessage("Profile photo uploaded successfully.");
    } catch (err) {
      setError(err.message);
    } finally {
      setUploadingPhoto(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    const splitList = (value) => value.split(",").map((item) => item.trim()).filter(Boolean);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/profiles/me", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          career_domain: form.career_domain,
          career_path: form.career_path,
          experience: form.experience,
          skills: splitList(form.skills),
          certifications: splitList(form.certifications),
          career_goals: form.career_goals,
          mentorship_interests: splitList(form.mentorship_interests),
          availability: form.availability,
          bio: form.bio || null,
          profile_picture_url: form.profile_picture_url.trim() || null,
          directory_visible: form.directory_visible,
        }),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail || "Could not save profile.")
        );
      }

      setProfile(data);
      const saved = { ...form, profile_picture_url: data.profile_picture_url || "" };
      setForm(saved);
      setSnapshot(JSON.stringify(saved));
      setMessage("Profile updated successfully.");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const selectedDomain = careerDomains.find((domain) => domain.id === form?.career_domain);
  const listOf = (value) => (value || "").split(",").map((item) => item.trim()).filter(Boolean);
  const checklist = form ? [
    { label: "Profile photo", done: Boolean(form.profile_picture_url) },
    { label: "Short bio", done: Boolean(form.bio.trim()) },
    { label: "Skills", done: listOf(form.skills).length > 0 },
    { label: "Career goals", done: Boolean(form.career_goals.trim()) },
    { label: "Certifications", done: listOf(form.certifications).length > 0 },
    { label: "Mentorship interests", done: listOf(form.mentorship_interests).length > 0 },
    { label: "Visible in the directory", done: form.directory_visible },
  ] : [];
  const completed = checklist.filter((item) => item.done).length;

  return (
    <div className="app">
      <Navbar />
      <main className="profile-page-shell">
        {error && <div className="page-alert" role="alert">{error}</div>}
        {message && <div className="profile-success" role="status">{message}</div>}

        {loading ? (
          <div className="profile-loading" role="status">Loading your profile…</div>
        ) : form ? (
          <>
          <section className="pf-hero" aria-label="Your profile">
            <div className="pf-hero-cover" aria-hidden="true" />
            <div className="pf-hero-avatar">
              <div className="profile-avatar-preview">
                <span className="profile-avatar-initials" aria-hidden="true">{initials(account?.full_name)}</span>
                {form.profile_picture_url ? (
                  <img src={form.profile_picture_url} alt="Your profile" onError={(event) => { event.currentTarget.style.display = "none"; }} />
                ) : null}
              </div>
              <label className="pf-camera" htmlFor="profile-photo-file" title="Change profile photo">
                <Camera size={16} aria-hidden="true" /><span className="visually-hidden">Change profile photo</span>
              </label>
              <input
                id="profile-photo-file"
                className="visually-hidden"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={(event) => setPhotoFile(event.target.files?.[0] || null)}
              />
            </div>
            <div className="pf-hero-body">
              <div className="pf-hero-id">
                <h1>{account?.full_name || "Your profile"}</h1>
                <p className="pf-hero-role">{[account?.community_role || account?.role, form.career_path].filter(Boolean).join(" · ")}</p>
                <p className="pf-hero-meta">{domainName(form.career_domain)}{account?.email ? ` · ${displayEmail(account.email)}` : ""}</p>
              </div>
              <div className="pf-meter" role="img" aria-label={`${completed} of ${checklist.length} profile sections complete`}>
                <strong>{completed} of {checklist.length}</strong>
                <span>sections complete</span>
                <div className="pf-meter-bar"><i style={{ width: `${(completed / checklist.length) * 100}%` }} /></div>
              </div>
            </div>
            {photoFile && (
              <form className="pf-upload" onSubmit={handlePhotoUpload}>
                <span>{photoFile.name}</span>
                <button className="btn btn-primary" type="submit" disabled={uploadingPhoto}>{uploadingPhoto ? "Uploading…" : "Upload photo"}</button>
                <button className="btn btn-outline" type="button" onClick={() => setPhotoFile(null)}>Cancel</button>
              </form>
            )}
            <dl className="pf-hero-stats">
              <div><dt>Directory</dt><dd>{form.directory_visible ? "Visible" : "Hidden"}</dd></div>
              <div><dt>Skills</dt><dd>{listOf(form.skills).length}</dd></div>
              <div><dt>Experience</dt><dd>{form.experience || "—"}</dd></div>
            </dl>
          </section>

          <div className="profile-editor-layout">
            <aside className="pf-side" aria-label="Profile preview">
              <section className="pf-card pf-preview">
                <h3>How others see you</h3>
                <p className="pf-preview-name">{account?.full_name}</p>
                <p className="pf-preview-role">{[account?.community_role || account?.role, form.career_path].filter(Boolean).join(" · ")}</p>
                {form.bio.trim() && <p className="pf-preview-bio">{form.bio.trim()}</p>}
                <div className="pf-chips">{listOf(form.skills).slice(0, 5).map((skill) => <span key={skill}>{skill}</span>)}</div>
                {!form.directory_visible && <p className="pf-preview-note">Hidden from the member directory. Turn it on in section 02 to appear there.</p>}
              </section>

              <section className="pf-card">
                <h3 className="pf-card-title">Profile checklist</h3>
                <ul className="pf-checklist" aria-label="Profile checklist">
                  {checklist.map((item) => (
                    <li key={item.label} className={item.done ? "is-done" : ""}>
                      {item.done ? <Check size={15} aria-hidden="true" /> : <Circle size={15} aria-hidden="true" />}
                      {item.label}
                    </li>
                  ))}
                </ul>
              </section>
            </aside>

            <form className="profile-editor" onSubmit={handleSubmit}>
              <section className="profile-editor-section">
                <div className="profile-section-heading">
                  <span>01</span>
                  <div><h2>Career direction</h2><p>Describe where you are and where you want to go.</p></div>
                </div>
                <div className="profile-edit-grid">
                  <label>Career domain
                    <select name="career_domain" value={form.career_domain} onChange={(event) => { handleChange(event); setForm((current) => ({ ...current, career_path: "" })); }} required>
                      <option value="">Select a career domain</option>
                      {!selectedDomain && form.career_domain && <option value={form.career_domain}>{form.career_domain}</option>}
                      {careerDomains.map((domain) => <option key={domain.id} value={domain.id}>{domain.name}</option>)}
                    </select>
                  </label>
                  <label>Career path
                    <select name="career_path" value={form.career_path} onChange={handleChange} required>
                      <option value="">{selectedDomain ? "Select a career path" : "Select a domain first"}</option>
                      {withCurrent(selectedDomain?.careers || [], form.career_path).map((path) => <option key={path} value={path}>{path}</option>)}
                    </select>
                  </label>
                  <label>Experience
                    <select name="experience" value={form.experience} onChange={handleChange} required>
                      <option value="">Select experience</option>
                      {withCurrent(experienceOptions, form.experience).map((item) => <option key={item}>{item}</option>)}
                    </select>
                  </label>
                  <label>Availability
                    <select name="availability" value={form.availability} onChange={handleChange} required>
                      <option value="">Select availability</option>
                      {withCurrent(availabilityOptions, form.availability).map((item) => <option key={item}>{item}</option>)}
                    </select>
                  </label>
                </div>
              </section>

              <section className="profile-editor-section">
                <div className="profile-section-heading">
                  <span>02</span>
                  <div><h2>Community directory</h2><p>Choose whether other signed-in mentors and mentees can discover your professional profile.</p></div>
                </div>
                <label className="directory-consent-control">
                  <input name="directory_visible" type="checkbox" checked={form.directory_visible} onChange={(event) => setForm((current) => ({ ...current, directory_visible: event.target.checked }))} />
                  <span><strong>Show my profile in the member directory</strong><small>Your name, role, career area, path, experience, skills, bio, and profile photo may be shown. Email, goals, certifications, and mentorship interests stay private.</small></span>
                </label>
              </section>

              <section className="profile-editor-section">
                <div className="profile-section-heading">
                  <span>03</span>
                  <div><h2>Skills and interests</h2><p>Separate multiple entries with commas.</p></div>
                </div>
                <div className="profile-edit-grid">
                  <label>Skills<input name="skills" value={form.skills} onChange={handleChange} required placeholder="e.g. Operations, Leadership" />
                    {listOf(form.skills).length > 0 && <span className="pf-chips">{listOf(form.skills).map((skill) => <span key={skill}>{skill}</span>)}</span>}
                  </label>
                  <label>Certifications<input name="certifications" value={form.certifications} onChange={handleChange} placeholder="e.g. PMP, CPA" /></label>
                  <label className="profile-edit-wide">Mentorship interests<input name="mentorship_interests" value={form.mentorship_interests} onChange={handleChange} placeholder="Topics you want to explore" /></label>
                </div>
              </section>

              <section className="profile-editor-section">
                <div className="profile-section-heading">
                  <span>04</span>
                  <div><h2>Goals and introduction</h2><p>Help the community understand your experience and goals.</p></div>
                </div>
                <div className="profile-edit-grid">
                  <label className="profile-edit-wide">Career goals<textarea name="career_goals" value={form.career_goals} onChange={handleChange} rows={4} required placeholder="What would you like to achieve next?" /><small className="pf-count">{form.career_goals.length} characters</small></label>
                  <label className="profile-edit-wide">Short bio<textarea name="bio" value={form.bio} onChange={handleChange} rows={4} placeholder="A short introduction about your professional journey" /><small className="pf-count">{form.bio.length} characters</small></label>
                </div>
              </section>

              <footer className={`profile-editor-footer ${dirty ? "is-dirty" : ""}`}>
                <span>{dirty ? "You have unsaved changes." : "Your profile helps create more relevant mentorship matches."}</span>
                <button className="btn btn-primary" type="submit" disabled={saving || !dirty}>
                  <Save size={16} aria-hidden="true" />{saving ? "Saving…" : "Save profile"}
                </button>
              </footer>
            </form>
          </div>
          </>
        ) : null}
      </main>
    </div>
  );
}
