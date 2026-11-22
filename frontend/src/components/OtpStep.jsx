import { useEffect, useRef, useState } from "react";
import { apiRequest } from "../services/api";

const RESEND_SECONDS = 30;

// Second step of password sign-in: the six-digit code emailed to the user.
// `onVerified` receives the access token once the code is accepted.
export default function OtpStep({ challenge, onVerified, onCancel }) {
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [cooldown, setCooldown] = useState(RESEND_SECONDS);
  const inputRef = useRef(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  useEffect(() => {
    if (cooldown <= 0) return undefined;
    const timer = window.setTimeout(() => setCooldown((value) => value - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [cooldown]);

  const submit = async (event) => {
    event.preventDefault();
    if (code.length !== 6) return;
    setBusy(true);
    setError("");
    try {
      const data = await apiRequest("/api/auth/login/verify-otp", {
        method: "POST",
        body: JSON.stringify({ challenge_token: challenge.challenge_token, code }),
        headers: {},
      });
      await onVerified(data.access_token);
    } catch (verifyError) {
      setError(verifyError.message || "We could not verify that code.");
      setCode("");
      inputRef.current?.focus();
      setBusy(false);
    }
  };

  const resend = async () => {
    setError("");
    setNotice("");
    try {
      const data = await apiRequest("/api/auth/login/resend-otp", {
        method: "POST",
        body: JSON.stringify({ challenge_token: challenge.challenge_token }),
        headers: {},
      });
      setNotice(data.email_sent === false
        ? "We could not deliver the email. In local development the new code is printed in the backend terminal."
        : "A new code is on its way.");
      setCooldown(RESEND_SECONDS);
    } catch (resendError) {
      setError(resendError.message || "We could not send a new code.");
    }
  };

  return (
    <form className="auth-form otp-step" onSubmit={submit}>
      <p className="otp-intro">
        {challenge.email_sent === false
          ? <>We could not deliver the email to <strong>{challenge.email_hint}</strong>. In local development the code is printed in the backend terminal.</>
          : <>We sent a six-digit code to <strong>{challenge.email_hint}</strong>. It expires in 10 minutes.</>}
      </p>

      <div className="auth-field">
        <label htmlFor="otp-code">Sign-in code</label>
        <input
          id="otp-code"
          ref={inputRef}
          className="otp-input"
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          pattern="[0-9]{6}"
          maxLength={6}
          placeholder="000000"
          value={code}
          onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
          required
        />
      </div>

      {notice && <p className="auth-notice" role="status">{notice}</p>}
      {error && <p className="auth-error" role="alert">{error}</p>}

      <button type="submit" className="btn btn-primary btn-full auth-submit" disabled={busy || code.length !== 6}>
        {busy ? "Verifying…" : "Verify and sign in"}
      </button>

      <div className="otp-actions">
        <button type="button" className="auth-text-button" onClick={resend} disabled={cooldown > 0}>
          {cooldown > 0 ? `Resend code in ${cooldown}s` : "Resend code"}
        </button>
        <button type="button" className="auth-text-button" onClick={onCancel}>Use a different account</button>
      </div>
    </form>
  );
}
