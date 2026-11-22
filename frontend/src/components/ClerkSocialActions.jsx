import { useState } from "react";
import { useAuth, useSignIn, useSignUp } from "@clerk/react";
import { useNavigate } from "react-router-dom";
import { apiRequest } from "../services/api";
import { saveClerkAuth } from "../services/authStorage";

const providers = [
  { label: "Google", strategy: "oauth_google" },
  { label: "Apple", strategy: "oauth_apple" },
  { label: "GitHub", strategy: "oauth_github" },
];

export default function ClerkSocialActions({ mode = "signin" }) {
  const { signIn } = useSignIn();
  const { signUp } = useSignUp();
  const { getToken } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");

  const start = async (provider) => {
    setLoading(provider.label);
    setError("");
    try {
      const authFlow = mode === "signup" ? signUp : signIn;
      const { error: flowError } = await authFlow.sso({
        strategy: provider.strategy,
        redirectCallbackUrl: "/sso-callback",
        redirectUrl: "/auth/complete",
      });
      if (flowError) throw flowError;
    } catch (authError) {
      const message = authError?.longMessage || authError?.message || `Unable to continue with ${provider.label}.`;
      if (/already signed in/i.test(message)) {
        try {
          const token = await getToken();
          if (!token) {
            setError("Clerk did not provide an active session token. Sign out of Clerk, then try again.");
            setLoading("");
            return;
          }
          const user = await apiRequest("/api/auth/clerk/session", {
            headers: { Authorization: `Bearer ${token}` },
          });
          saveClerkAuth(token, user);
          const destination = user.role === "admin" ? "/admin" : user.role === "mentor" ? "/mentor-workspace" : "/mentors";
          navigate(destination, { replace: true });
        } catch (sessionError) {
          if (sessionError.message?.includes("Complete AlumniConnect account setup")) {
            navigate("/clerk-onboarding", { replace: true });
          } else {
            setError(`Clerk is signed in, but AlumniConnect could not verify the session: ${sessionError.message || "Please try again."}`);
            setLoading("");
          }
        }
        return;
      }
      setError(message);
      setLoading("");
    }
  };

  return <>
    <div className="auth-social-grid">
      {providers.map((provider) => <button
        key={provider.strategy}
        type="button"
        className={`auth-social-button auth-social-${provider.label.toLowerCase()}`}
        onClick={() => start(provider)}
        disabled={Boolean(loading)}
        aria-label={`Continue with ${provider.label}`}
        title={`Continue with ${provider.label}`}
      >
        {loading === provider.label ? <span className="auth-social-loading">…</span> : <ProviderLogo provider={provider.label} />}
      </button>)}
    </div>
    {error && <p className="auth-error" role="alert">{error}</p>}
  </>;
}

function ProviderLogo({ provider }) {
  if (provider === "Google") return <svg aria-hidden="true" viewBox="0 0 48 48" width="20" height="20">
    <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.73 7.18l7.64 5.93c4.46-4.12 7.13-10.2 7.13-17.58Z" />
    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.9-5.79l-7.64-5.93c-2.12 1.42-4.84 2.27-8.26 2.27-6.26 0-11.57-4.22-13.46-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48Z" />
    <path fill="#FBBC05" d="M10.53 28.59a14.4 14.4 0 0 1 0-9.18l-7.98-6.19a23.9 23.9 0 0 0 0 21.56l7.98-6.19Z" />
    <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5Z" />
  </svg>;
  if (provider === "Apple") return <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
    <path d="M16.37 12.3c.02 2.2 1.93 2.93 1.95 2.94-.02.05-.3 1.04-.99 2.06-.6.89-1.22 1.77-2.2 1.79-.96.02-1.27-.58-2.37-.58-1.1 0-1.44.56-2.35.6-.94.04-1.65-.96-2.25-1.84-1.22-1.77-2.15-5-.9-7.17.62-1.08 1.72-1.76 2.9-1.78.9-.02 1.75.64 2.3.64.54 0 1.56-.79 2.63-.67.45.02 1.72.18 2.54 1.37-.07.04-1.52.89-1.5 2.64ZM14.64 6.15c.5-.61.83-1.46.74-2.3-.72.03-1.59.48-2.1 1.1-.46.54-.86 1.4-.75 2.22.8.06 1.61-.4 2.11-1.02Z" />
  </svg>;
  return <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
    <path d="M12 .8a11.2 11.2 0 0 0-3.54 21.83c.56.1.77-.24.77-.54v-2.1c-3.13.68-3.79-1.33-3.79-1.33-.51-1.3-1.25-1.65-1.25-1.65-1.02-.7.08-.69.08-.69 1.13.08 1.73 1.16 1.73 1.16 1 .1.8 2.32 3.37 1.74.1-.73.4-1.22.72-1.5-2.5-.28-5.13-1.25-5.13-5.56 0-1.23.44-2.23 1.16-3.02-.12-.29-.5-1.43.11-2.98 0 0 .95-.3 3.08 1.15a10.7 10.7 0 0 1 5.6 0c2.13-1.45 3.07-1.15 3.07-1.15.61 1.55.23 2.69.12 2.98.72.79 1.15 1.79 1.15 3.02 0 4.32-2.64 5.28-5.15 5.56.41.35.77 1.03.77 2.08v3.09c0 .3.2.65.78.54A11.2 11.2 0 0 0 12 .8Z" />
  </svg>;
}
