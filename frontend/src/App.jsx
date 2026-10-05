import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  Navigate,
} from "react-router-dom";

import { useEffect, useState } from "react";

import {
  ArrowRight,
  Search,
  SlidersHorizontal,
  Plane,
} from "lucide-react";

import { careerDomains } from "./data/careers";

/* =========================
   NAVBAR
========================= */

function Navbar() {
  return (
    <header className="navbar">
      <Link to="/" className="brand">
        <span className="brand-mark">A</span>
        <span>Kenya Airways AlumniConnect</span>
      </Link>

      <nav className="nav-links">
        <Link to="/">Home</Link>
        <Link to="/mentors">Discover Mentors</Link>
        <Link to="/knowledge">Knowledge Hub</Link>
      </nav>

      <div className="nav-actions">
        <Link to="/login" className="btn btn-outline">
          Log in
        </Link>

        <Link to="/register" className="btn btn-primary">
          Get started
        </Link>
      </div>
    </header>
  );
}

/* =========================
   LANDING PAGE
========================= */

function LandingPage() {
  return (
    <div className="app">
      <Navbar />

      <main>

        {/* HERO */}

        <section className="landing-hero">

          <div className="hero-content">

            <span className="eyebrow">
              KENYA AIRWAYS • ALUMNI • MENTORSHIP
            </span>

            <h1>
              Connect experience
              <br />
              with ambition.
            </h1>

            <p>
              Kenya Airways AlumniConnect creates meaningful professional
              connections between experienced alumni, aviation professionals
              and the next generation of talent.
            </p>

            <div className="hero-buttons">
              <Link to="/mentors" className="btn btn-primary btn-large">
                Find a mentor
                <ArrowRight size={17} />
              </Link>

              <Link to="/register" className="btn btn-outline btn-large">
                Become a mentor
              </Link>
            </div>

          </div>

          <div className="hero-side">

            <div className="hero-card">

              <div className="hero-card-label">
                SEMANTIC MENTOR MATCH
              </div>

              <div className="hero-match">

                <div className="mentor-avatar">
                  AM
                </div>

                <div>
                  <h3>Recommended Mentor</h3>
                  <p>Technology & Digital</p>
                </div>

                <strong>92%</strong>

              </div>

              <div className="match-bar">
                <div />
              </div>

              <p className="match-text">
                Matched across skills, experience, career interests and
                professional goals.
              </p>

            </div>

            <div className="hero-stat-row">

              <div>
                <strong>Semantic</strong>
                <span>Profile matching</span>
              </div>

              <div>
                <strong>Career</strong>
                <span>Development</span>
              </div>

              <div>
                <strong>Knowledge</strong>
                <span>Sharing</span>
              </div>

            </div>

          </div>

        </section>


        {/* HOW IT WORKS */}

        <section className="process-section">

          <div className="section-intro">
            <span className="section-number">01</span>

            <div>
              <h2>How AlumniConnect works</h2>

              <p>
                A structured mentorship journey built around professional
                goals and meaningful experience.
              </p>
            </div>
          </div>


          <div className="process-grid">

            <div className="process-card">
              <span>01</span>
              <h3>Create your profile</h3>

              <p>
                Build a professional profile containing your experience,
                skills and career interests.
              </p>
            </div>

            <div className="process-card">
              <span>02</span>
              <h3>Define your goals</h3>

              <p>
                Tell the platform where you want your career to go and the
                experience you are looking for.
              </p>
            </div>

            <div className="process-card featured">
              <span>03</span>
              <h3>Semantic matching</h3>

              <p>
                Sentence-BERT analyses profile information to identify
                meaningful mentor compatibility.
              </p>
            </div>

            <div className="process-card">
              <span>04</span>
              <h3>Connect & engage</h3>

              <p>
                Review recommendations, understand the match and request
                mentorship.
              </p>
            </div>

          </div>

        </section>


        {/* CAREER AREAS */}

        <section className="career-section">

          <div className="section-intro">

            <span className="section-number">02</span>

            <div>
              <h2>Explore career pathways</h2>

              <p>
                Discover professional directions across the aviation
                ecosystem.
              </p>
            </div>

          </div>


          <div className="career-grid">

            {careerDomains.map((domain) => (

              <div className="career-card" key={domain.id}>

                <div className="career-card-top">
                  <h3>{domain.name}</h3>
                  <ArrowRight size={16} />
                </div>

                <div className="career-tags">

                  {domain.careers.slice(0, 4).map((career) => (
                    <span key={career}>{career}</span>
                  ))}

                </div>

              </div>

            ))}

          </div>

        </section>


        {/* CTA */}

        <section className="landing-cta">

          <Plane size={24} />

          <h2>
            Your experience can
            <br />
            shape someone's next chapter.
          </h2>

          <Link to="/register" className="btn btn-light btn-large">
            Join AlumniConnect
            <ArrowRight size={17} />
          </Link>

        </section>

      </main>


      <footer>

        <div className="brand">
          <span className="brand-mark">A</span>
          <span>Kenya Airways AlumniConnect</span>
        </div>

        <span>Professional mentorship & knowledge sharing</span>

        <span>© 2026</span>

      </footer>

    </div>
  );
}


/* =========================
   DISCOVER MENTORS
========================= */

function MentorsPage() {

  const [mentors, setMentors] = useState([]);
  const [loading, setLoading] = useState(true);
  const params = new URLSearchParams(window.location.search);
  const menteeId = params.get("mentee") || "1";

  useEffect(() => {

    fetch(`http://127.0.0.1:8000/api/matches/${menteeId}`)

      .then((response) => {

        if (!response.ok) {
          throw new Error("Failed to fetch mentor matches");
        }

        return response.json();
      })

      .then((data) => {
        setMentors(data.matches);
      })

      .catch((error) => {
        console.error("Failed to load mentors:", error);
      })

      .finally(() => {
        setLoading(false);
      });

  }, [menteeId]);


  if (loading) {
    return (
      <div className="simple-page">
        <div className="simple-card">

          <h1>Finding your mentors...</h1>

          <p>
            Analysing your profile using semantic matching.
          </p>

        </div>
      </div>
    );
  }


  return (
    <div className="app">

      <Navbar />

      <main className="mentors-page">

        <div className="mentors-header">

          <div>

            <span className="eyebrow">
              SEMANTIC MENTOR DISCOVERY
            </span>

            <h1>Recommended Mentors</h1>

            <p>
              Discover mentors whose experience and competencies align with
              your career goals.
            </p>

          </div>

        </div>


        {/* FILTERS */}

        <div className="mentor-filters">

          <div className="search-box">
            <Search size={17} />
            <input placeholder="Search keywords..." />
          </div>

          <select>
            <option>Aviation discipline</option>

            {careerDomains.map((domain) => (
              <option key={domain.id}>
                {domain.name}
              </option>
            ))}

          </select>

          <select>
            <option>Required competency</option>
            <option>Leadership</option>
            <option>Technical</option>
            <option>Communication</option>
            <option>Management</option>
          </select>

          <button className="filter-button">
            <SlidersHorizontal size={16} />
            Filters
          </button>

        </div>


        {/* RESULTS */}

        <div className="mentor-results">

          {mentors.map((mentor) => {

            const initials = mentor.career_path
              .split(" ")
              .map((word) => word[0])
              .join("")
              .slice(0, 2)
              .toUpperCase();

            return (

              <div
                className="mentor-result-card"
                key={mentor.id}
              >

                <div className="mentor-card-header">

                  <div className="mentor-identity">

                    <div className="mentor-avatar large">
                      {initials}
                    </div>

                    <div>

                      <h3>{mentor.career_path}</h3>

                      <p>
                        {mentor.career_domain}
                      </p>

                    </div>

                  </div>


                  <div className="cosine-score">

                    <strong>
                      {mentor.similarity_score}%
                    </strong>

                    <span>
                      COSINE MATCH
                    </span>

                  </div>

                </div>


                <div className="mentor-meta">

                  <span>
                    {mentor.experience}
                  </span>

                  <span>
                    {mentor.availability}
                  </span>

                </div>


                <div className="rationale">

                  <strong>
                    Sentence-BERT similarity rationale
                  </strong>

                  <p>
                    Semantic similarity was calculated from career direction,
                    skills, experience, availability and professional goals.
                  </p>

                </div>


                <div className="competencies">

                  {mentor.skills.map((skill) => (

                    <span key={skill.trim()}>
                      {skill.trim()}
                    </span>

                  ))}

                </div>


                <div className="mentor-card-actions">

                  <Link
                    to="/mentor-profile"
                    className="btn btn-outline"
                  >
                    View Profile
                  </Link>

                  <button className="btn btn-primary">
                    Request Mentorship
                  </button>

                </div>

              </div>

            );

          })}

        </div>

      </main>

    </div>
  );
}


/* =========================
   LOGIN
========================= */

function LoginPage() {

  return (

    <div className="simple-page">

      <div className="simple-card">

        <Link to="/" className="brand">
          <span className="brand-mark">A</span>
          <span>AlumniConnect</span>
        </Link>

        <h1>Welcome back.</h1>

        <p>
          Sign in to your AlumniConnect account.
        </p>

        <input placeholder="Email address" />

        <input
          type="password"
          placeholder="Password"
        />

        <button className="btn btn-primary btn-full">
          Sign in
        </button>

      </div>

    </div>
  );
}


/* =========================
   REGISTER
========================= */

function RegisterPage() {
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

  const selectedDomain = careerDomains.find(
    (item) => item.id === domain
  );

  const handleSubmit = async (event) => {
    event.preventDefault();

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
      const response = await fetch(
        "http://127.0.0.1:8000/api/auth/register",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(registrationData),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();

        throw new Error(
          errorData.detail || "Registration failed"
        );
      }

      await response.json();

      window.location.href = "/login";
    } catch (error) {
      console.error("Registration failed:", error);

      alert(
        error.message ||
          "We couldn't create your account. Please make sure the AlumniConnect backend is running."
      );
    }
  };

  return (

    <div className="profile-page">

      <div className="profile-container">

        <div className="profile-header">

          <Link to="/" className="brand">
            <span className="brand-mark">A</span>
            <span>Kenya Airways AlumniConnect</span>
          </Link>

          <span className="profile-step">
            PROFILE SETUP • 01 / 01
          </span>

        </div>


        <div className="profile-intro">

          <span className="eyebrow">
            BUILD YOUR PROFESSIONAL PROFILE
          </span>

          <h1>
            Tell us where
            <br />
            you're headed.
          </h1>

          <p>
            Your profile helps AlumniConnect identify mentors whose
            experience, competencies and career direction align with yours.
          </p>

        </div>


        <form
          className="profile-form"
          onSubmit={handleSubmit}
        >

        <section className="form-section">
  <div className="form-section-heading">
    <span>01</span>
    <div>
      <h2>Your account</h2>
      <p>Create your AlumniConnect account.</p>
    </div>
  </div>

  <div className="form-grid">
    <div className="field">
      <label>Full name</label>
      <input
        type="text"
        value={fullName}
        onChange={(event) => setFullName(event.target.value)}
        placeholder="e.g. Joy Senetwo"
        required
      />
    </div>

    <div className="field">
      <label>Email address</label>
      <input
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        placeholder="you@example.com"
        required
      />
    </div>

    <div className="field">
      <label>Password</label>
      <input
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        placeholder="At least 8 characters"
        minLength="8"
        required
      />
    </div>
  </div>
</section>


          {/* ROLE */}

          <section className="form-section">

            <div className="form-section-heading">

              <span>01</span>

              <div>

                <h2>Your role</h2>

                <p>
                  How will you participate in AlumniConnect?
                </p>

              </div>

            </div>


            <div className="role-grid">

              <button
                type="button"
                className={`role-card ${
                  role === "mentee" ? "selected" : ""
                }`}
                onClick={() => setRole("mentee")}
              >

                <strong>Mentee</strong>

                <span>
                  I'm looking for guidance and professional mentorship.
                </span>

              </button>


              <button
                type="button"
                className={`role-card ${
                  role === "mentor" ? "selected" : ""
                }`}
                onClick={() => setRole("mentor")}
              >

                <strong>Mentor</strong>

                <span>
                  I want to share my experience and support others.
                </span>

              </button>

            </div>

          </section>


          {/* CAREER */}

          <section className="form-section">

            <div className="form-section-heading">

              <span>02</span>

              <div>

                <h2>Career direction</h2>

                <p>
                  Tell us which professional path interests you.
                </p>

              </div>

            </div>


            <div className="form-grid">

              <div className="field">

                <label>
                  Career domain
                </label>

                <select
                  value={domain}
                  onChange={(event) => {
                    setDomain(event.target.value);
                    setCareer("");
                  }}
                  required
                >

                  <option value="">
                    Select a career domain
                  </option>

                  {careerDomains.map((item) => (

                    <option
                      value={item.id}
                      key={item.id}
                    >
                      {item.name}
                    </option>

                  ))}

                </select>

              </div>


              <div className="field">

                <label>
                  Career path
                </label>

                <select
                  value={career}
                  onChange={(event) =>
                    setCareer(event.target.value)
                  }
                  disabled={!selectedDomain}
                  required
                >

                  <option value="">
                    {selectedDomain
                      ? "Select a career path"
                      : "Select a domain first"}
                  </option>

                  {selectedDomain?.careers.map((item) => (

                    <option
                      value={item}
                      key={item}
                    >
                      {item}
                    </option>

                  ))}

                </select>

              </div>


              <div className="field">

                <label>
                  Professional experience
                </label>

                <select
                  value={experience}
                  onChange={(event) =>
                    setExperience(event.target.value)
                  }
                  required
                >

                  <option value="">
                    Select experience
                  </option>

                  <option>
                    Student / Graduate
                  </option>

                  <option>
                    0–2 years
                  </option>

                  <option>
                    3–5 years
                  </option>

                  <option>
                    6–10 years
                  </option>

                  <option>
                    10+ years
                  </option>

                </select>

              </div>

            </div>

          </section>


          {/* SKILLS */}

          <section className="form-section">

            <div className="form-section-heading">

              <span>03</span>

              <div>

                <h2>Skills & experience</h2>

                <p>
                  These details will contribute to your semantic profile.
                </p>

              </div>

            </div>


            <div className="field">

              <label>
                Skills
              </label>

              <input
                type="text"
                value={skills}
                onChange={(event) =>
                  setSkills(event.target.value)
                }
                placeholder="e.g. Python, Cloud Computing, Leadership, Aircraft Systems"
                required
              />

              <small>
                Separate multiple skills with commas.
              </small>

            </div>

          </section>


          {/* GOALS */}

          <section className="form-section">

            <div className="form-section-heading">

              <span>04</span>

              <div>

                <h2>Career goals</h2>

                <p>
                  Describe what you want to achieve professionally.
                </p>

              </div>

            </div>


            <div className="field">

              <label>
                What are you hoping to achieve?
              </label>

              <textarea
                value={goals}
                onChange={(event) =>
                  setGoals(event.target.value)
                }
                placeholder="Tell us about the career direction, knowledge or experience you are looking for..."
                rows="5"
                required
              />

            </div>


            <div className="field">

              <label>
                Mentorship availability
              </label>

              <select
                value={availability}
                onChange={(event) =>
                  setAvailability(event.target.value)
                }
                required
              >

                <option value="">
                  Select availability
                </option>

                <option>
                  Weekday mornings
                </option>

                <option>
                  Weekday afternoons
                </option>

                <option>
                  Weekday evenings
                </option>

                <option>
                  Weekends
                </option>

                <option>
                  Flexible
                </option>

              </select>

            </div>

          </section>


          <div className="profile-submit">

            <div>

              <strong>
                Ready to discover your matches?
              </strong>

              <span>
                You can update your profile later.
              </span>

            </div>

            <button
              type="submit"
              className="btn btn-primary btn-large"
            >

              Create profile

              <ArrowRight size={17} />

            </button>

          </div>

        </form>

      </div>

    </div>
  );
}


/* =========================
   PLACEHOLDERS
========================= */

function Placeholder({ title }) {

  return (

    <div className="simple-page">

      <div className="simple-card">

        <Link to="/" className="brand">
          <span className="brand-mark">A</span>
          <span>AlumniConnect</span>
        </Link>

        <h1>{title}</h1>

        <p>
          This module is coming next.
        </p>

        <Link to="/" className="btn btn-primary">
          Back home
        </Link>

      </div>

    </div>
  );
}


/* =========================
   ROUTER
========================= */

function App() {

  return (

    <BrowserRouter>

      <Routes>

        <Route
          path="/"
          element={<LandingPage />}
        />

        <Route
          path="/mentors"
          element={<MentorsPage />}
        />

        <Route
          path="/login"
          element={<LoginPage />}
        />

        <Route
          path="/register"
          element={<RegisterPage />}
        />

        <Route
          path="/knowledge"
          element={<Placeholder title="Knowledge Hub" />}
        />

        <Route
          path="/mentor"
          element={<Placeholder title="Mentor Workspace" />}
        />

        <Route
          path="/admin"
          element={<Placeholder title="Administrator Dashboard" />}
        />

        <Route
          path="/mentor-profile"
          element={<Placeholder title="Mentor Profile" />}
        />

        <Route
          path="*"
          element={<Navigate to="/" replace />}
        />

      </Routes>

    </BrowserRouter>
  );
}


export default App;