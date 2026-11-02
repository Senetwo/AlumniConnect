import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { apiRequest } from "../services/api";
import Brand from "../components/Brand";

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [complete, setComplete] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");
    if (password !== confirmation) {
      setError("The passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      const response = await apiRequest("/api/auth/password-reset/confirm", {
        method: "POST",
        body: JSON.stringify({ token, new_password: password }),
        headers: {},
      });
      setMessage(response.message);
      setComplete(true);
    } catch (requestError) {
      setError(requestError.message || "This reset link could not be used. Request a new one.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="verify-page">
      <section className="verify-card reset-password-card">
        <Brand />
        <h1>{complete ? "Password updated" : "Choose a new password"}</h1>
        {complete ? (
          <>
            <p role="status">{message}</p>
            <Link className="btn btn-primary" to="/login">Continue to sign in</Link>
          </>
        ) : (
          <>
            <p>This link expires one hour after it was requested.</p>
            <form className="auth-form" onSubmit={handleSubmit}>
              <label className="reset-password-field">New password
                <input type="password" autoComplete="new-password" minLength={8} maxLength={128} required value={password} onChange={(event) => setPassword(event.target.value)} />
              </label>
              <label className="reset-password-field">Confirm new password
                <input type="password" autoComplete="new-password" minLength={8} maxLength={128} required value={confirmation} onChange={(event) => setConfirmation(event.target.value)} />
              </label>
              {error && <p className="auth-error" role="alert">{error}</p>}
              <button className="btn btn-primary btn-full" type="submit" disabled={loading || !token}>
                {loading ? "Updating password…" : "Set new password"}
              </button>
              {!token && <p className="auth-error" role="alert">This link is missing its reset token. Request another link from sign-in.</p>}
            </form>
          </>
        )}
      </section>
    </main>
  );
}
