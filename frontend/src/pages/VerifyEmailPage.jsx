import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { apiRequest } from "../services/api";
import Brand from "../components/Brand";

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [message, setMessage] = useState("Verifying your email address…");
  const [isError, setIsError] = useState(false);
  const requestedToken = useRef(null);

  useEffect(() => {
    // Verification tokens are single use. React StrictMode runs effects twice in
    // development, so only send the request once per token.
    if (!token || requestedToken.current === token) return;
    requestedToken.current = token;
    apiRequest("/api/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ token }),
      headers: {},
    }).then((data) => {
      setMessage(data.message || "Your email has been verified.");
    }).catch((error) => {
      setMessage(error.message || "We could not verify this link. Request a new email and try again.");
      setIsError(true);
    });
  }, [token]);

  const incompleteLink = !token;
  const errorState = isError || incompleteLink;

  return (
    <main className="verify-page">
      <section className="verify-card">
        <Brand />
        <span className={`verify-status ${errorState ? "is-error" : ""}`} aria-hidden="true">{errorState ? "!" : "✓"}</span>
        <h1>{errorState ? "Verification link issue" : "Email verification"}</h1>
        <p role="status">{incompleteLink ? "This verification link is incomplete. Request a new email and use the latest link." : message}</p>
        <Link className="btn btn-primary" to="/login">Continue to sign in</Link>
      </section>
    </main>
  );
}
