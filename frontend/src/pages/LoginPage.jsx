
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { apiRequest } from "../services/api";
import { saveAuth } from "../services/authStorage";
import ClerkSocialActions from "../components/ClerkSocialActions";
import OtpStep from "../components/OtpStep";
import ThemeToggle from "../components/ThemeToggle";
import Brand from "../components/Brand";
import kenyaAirwaysLogoWhite from "../assets/brand/kenya-airways-logo-white.svg";

function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState(location.state?.email || "");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState(location.state?.verificationPending
    ? location.state?.notice || "Your account was created, but the verification message could not be delivered. Use the one-time link printed in the backend terminal."
    : location.state?.registered
      ? "Your account was created. Verify your email using the link we sent before signing in."
      : "");
  const [challenge, setChallenge] = useState(null);
  const [forgotOpen, setForgotOpen] = useState(false);
  const [forgotEmail, setForgotEmail] = useState(location.state?.email || "");
  const [forgotMessage, setForgotMessage] = useState("");
  const [forgotError, setForgotError] = useState("");
  const [forgotLoading, setForgotLoading] = useState(false);

  const handleLogin = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await apiRequest("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      if (data.mfa_required) {
        setChallenge(data);
        setPassword("");
        return;
      }
      await completeSignIn(data.access_token);
    } catch (err) {
      setError(
        err.message || "We couldn't sign you in. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const completeSignIn = async (token) => {
    if (!token) {
      throw new Error("The server did not return an access token.");
    }

    const userData = await apiRequest("/api/auth/me", {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    // Save the authentication data using the authStorage service.
    saveAuth(token, userData, rememberMe);

    if (userData.role === "admin") {
      navigate("/admin");
    } else if (userData.role === "mentor") {
      navigate("/mentor-workspace");
    } else {
      navigate("/mentors");
    }
  };

  const handleResendVerification = async () => {
    if (!email) {
      setError("Enter your email address first, then request a new verification email.");
      return;
    }
    try {
      const response = await apiRequest("/api/auth/resend-verification", {
        method: "POST",
        body: JSON.stringify({ email }),
        headers: {},
      });
      setNotice(response.message);
      setError("");
    } catch (requestError) {
      setError(requestError.message || "We could not resend the verification email.");
    }
  };

  const handlePasswordResetRequest = async (event) => {
    event.preventDefault();
    setForgotError("");
    setForgotMessage("");
    setForgotLoading(true);
    try {
      const response = await apiRequest("/api/auth/password-reset/request", {
        method: "POST",
        body: JSON.stringify({ email: forgotEmail }),
        headers: {},
      });
      setForgotMessage(response.message);
    } catch (requestError) {
      setForgotError(requestError.message || "We could not send a reset email. Try again shortly.");
    } finally {
      setForgotLoading(false);
    }
  };

  return (
    <main className="auth-page">
      <ThemeToggle floating />
      <section className="auth-showcase">
        <Brand inverse className="auth-brand" />

        <div className="auth-showcase-content">
          <span className="auth-eyebrow">
            YOUR NEXT CHAPTER STARTS HERE
          </span>

          <h1>
            Great things happen when
            <span> experience meets ambition.</span>
          </h1>

          <p>
            Reconnect with your community, learn from experienced
            professionals, and turn meaningful conversations into
            career opportunities.
          </p>

          <div className="auth-feature-list">
            <div className="auth-feature">
              <span className="auth-feature-icon">01</span>
              <div>
                <strong>Find your people</strong>
                <p>Discover mentors aligned with your goals.</p>
              </div>
            </div>

            <div className="auth-feature">
              <span className="auth-feature-icon">02</span>
              <div>
                <strong>Share what you know</strong>
                <p>Build connections that move careers forward.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="auth-showcase-footer">
          <img className="auth-partner-logo" src={kenyaAirwaysLogoWhite} alt="Kenya Airways" />
          A community built on experience, opportunity, and connection.
        </div>
      </section>

      <section className="auth-panel">
        <div className="auth-form-wrap">
          <div className="auth-mobile-brand">
            <Brand />
          </div>

          <div className="auth-heading">
            <span className="auth-eyebrow">{challenge ? "ONE MORE STEP" : "WELCOME BACK"}</span>
            <h2>{challenge ? "Check your email" : "Sign in to your account"}</h2>
            <p>
              {challenge
                ? "Enter the code we sent to confirm it is you."
                : "Pick up where you left off. Your next connection awaits."}
            </p>
            <div className="auth-security-note"><span />Secure access for alumni, mentors, and mentees</div>
          </div>

          {notice && <p className="auth-notice" role="status">{notice}</p>}
          {(location.state?.verificationPending || location.state?.registered) && (
            <button className="auth-text-button auth-resend-button" type="button" onClick={handleResendVerification}>
              Resend verification email
            </button>
          )}

          {challenge ? <OtpStep challenge={challenge} onVerified={completeSignIn} onCancel={() => setChallenge(null)} /> : <>
          <form className="auth-form" onSubmit={handleLogin}>
            <div className="auth-field">
              <label htmlFor="login-email">Email address</label>
              <input
                id="login-email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                autoComplete="email"
                required
              />
            </div>

            <div className="auth-field">
              <div className="auth-label-row">
                <label htmlFor="login-password">Password</label>
                <button
                  className="auth-text-button"
                  type="button"
                  onClick={() => {
                    setForgotEmail(email);
                    setForgotOpen((open) => !open);
                    setForgotMessage("");
                    setForgotError("");
                  }}
                >
                  Forgot password?
                </button>
              </div>

              <div className="auth-password-wrap">
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  className="auth-password-toggle"
                  onClick={() => setShowPassword((visible) => !visible)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            {forgotOpen && (
              <div className="auth-forgot-panel">
                <strong>Reset your password</strong>
                <p>We’ll email a one-hour reset link if this address has an account.</p>
                <input
                  type="email"
                  aria-label="Email address for password reset"
                  placeholder="you@example.com"
                  autoComplete="email"
                  value={forgotEmail}
                  onChange={(event) => setForgotEmail(event.target.value)}
                  required
                />
                {forgotMessage && <p className="auth-notice" role="status">{forgotMessage}</p>}
                {forgotError && <p className="auth-error" role="alert">{forgotError}</p>}
                <button className="btn btn-outline" type="button" disabled={forgotLoading || !forgotEmail} onClick={handlePasswordResetRequest}>
                  {forgotLoading ? "Sending…" : "Send reset link"}
                </button>
              </div>
            )}

            <label className="auth-remember">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(event) => setRememberMe(event.target.checked)}
              />
              <span>Keep me signed in on this device</span>
            </label>

            {error && (
              <p className="auth-error" role="alert">
                {error}
              </p>
            )}
            {error.toLowerCase().includes("verify your email") && (
              <button className="auth-text-button auth-resend-button" type="button" onClick={handleResendVerification}>
                Resend verification email
              </button>
            )}

            <button
              type="submit"
              className="btn btn-primary btn-full auth-submit"
              disabled={loading}
            >
              {loading ? "Signing you in..." : "Sign in"}
              {!loading && <span aria-hidden="true">→</span>}
            </button>
          </form>

          <div className="auth-divider">
            <span>OR CONTINUE WITH</span>
          </div>

          {import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
            ? <ClerkSocialActions />
            : <p className="auth-legal">Social sign-in is unavailable until Clerk is configured.</p>}

          <p className="auth-register-prompt">
            Don't have an account? <Link to="/register">Create one</Link>
          </p>

          <p className="auth-legal">
            By signing in, you agree to use AlumniConnect respectfully
            and professionally.
          </p>
          </>}
        </div>
      </section>
    </main>
  );
}

export default LoginPage;

