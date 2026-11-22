import { BrowserRouter, Routes, Route, Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { useAuth, useClerk, HandleSSOCallback } from "@clerk/react";
import ProtectedRoute from "./components/ProtectedRoute";
import SiteFooter from "./components/SiteFooter";
import NotificationsPage from "./pages/NotificationsPage";
import LandingPage from "./pages/LandingPage";
import MentorsPage from "./pages/MentorsPage";
import RegisterPage from "./pages/RegisterPage";
import LoginPage from "./pages/LoginPage";
import MyProfilePage from "./pages/MyProfilePage";
import MentorWorkspacePage from "./pages/MentorWorkspacePage";
import MyMentorshipsPage from "./pages/MyMentorshipsPage";
import AvailabilityPage from "./pages/AvailabilityPage";
import BookingPage from "./pages/BookingPage";
import ChatsPage from "./pages/ChatsPage";
import KnowledgePage from "./pages/KnowledgePage";
import AdminKnowledgePage from "./pages/AdminKnowledgePage";
import AdminDashboard from "./pages/AdminDashboard";
import MentorProfilePage from "./pages/MentorProfilePage";
import DirectoryPage from "./pages/DirectoryPage";
import AdminAnnouncementsPage from "./pages/AdminAnnouncementsPage";
import AdminCommunityPage from "./pages/AdminCommunityPage";
import AdminUsersPage from "./pages/AdminUsersPage";
import AdminOperationsPage from "./pages/AdminOperationsPage";
import WorkspaceLayout from "./pages/workspace/WorkspaceLayout";
import OverviewTab from "./pages/workspace/OverviewTab";
import SessionsTab from "./pages/workspace/SessionsTab";
import SessionDetailPage from "./pages/workspace/SessionDetailPage";
import NotesTab from "./pages/workspace/NotesTab";
import GoalsTab from "./pages/workspace/GoalsTab";
import ProgressTab from "./pages/workspace/ProgressTab";
import VerifyEmailPage from "./pages/VerifyEmailPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import { apiRequest } from "./services/api";
import { clearAuth, getAuth, saveClerkAuth, saveAuth, setClerkSession } from "./services/authStorage";
import ClerkOnboardingPage from "./pages/ClerkOnboardingPage";

function SessionRoleSync() {
  const location = useLocation();
  const navigate = useNavigate();
  const syncedToken = useRef(null);
  const inFlightToken = useRef(null);

  useEffect(() => {
    const auth = getAuth();
    if (!auth || syncedToken.current === auth.token || inFlightToken.current === auth.token) return;
    inFlightToken.current = auth.token;
    apiRequest("/api/auth/me").then(user => {
      inFlightToken.current = null;
      if (getAuth()?.token !== auth.token) return;
      syncedToken.current = auth.token;
      const roleChanged = user.role !== auth.user.role;
      saveAuth(auth.token, user, auth.storage === localStorage);
      if (roleChanged) {
        const home = user.role === "admin" ? "/admin" : user.role === "mentor" ? "/mentor-workspace" : "/mentors";
        navigate(home, { replace: true });
      } else {
        navigate(`${location.pathname}${location.search}`, { replace: true });
      }
    }).catch(error => {
      inFlightToken.current = null;
      if (getAuth()?.token !== auth.token) return;
      if (error.message?.includes("session may have expired")) {
        clearAuth();
        navigate("/login", { replace: true });
      }
    });
  }, [location.pathname, location.search, navigate]);

  return null;
}

function ClerkSessionBridge() {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const clerk = useClerk();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    setClerkSession(getToken, () => clerk.signOut());
    return () => setClerkSession(null, null);
  }, [getToken, clerk]);

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;
    // Keep the login and registration screens available even if Clerk has a
    // cached session. The user may be switching accounts or using password
    // sign-in, so only sync Clerk on application routes / the callback flow.
    if (["/login", "/register", "/auth/complete", "/clerk-onboarding"].includes(location.pathname)) return;
    const savedAuth = getAuth();
    // A password sign-in may coexist with a Clerk browser session. Do not let
    // the background bridge replace the explicitly selected AlumniConnect
    // account with the cached Clerk identity.
    if (savedAuth && !savedAuth.clerk) return;
    let cancelled = false;
    (async () => {
      try {
        const token = await getToken();
        const user = await apiRequest("/api/auth/clerk/session", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (cancelled) return;
        saveClerkAuth(token, user);
      } catch (error) {
        if (cancelled) return;
        if (error.message?.includes("Complete AlumniConnect account setup")) {
          navigate("/clerk-onboarding", { replace: true });
        }
      }
    })();
    return () => { cancelled = true; };
  }, [isLoaded, isSignedIn, getToken, location.pathname, navigate]);

  return null;
}

function ClerkAuthComplete() {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!isLoaded) return;
    if (!isSignedIn) {
      navigate("/login", { replace: true });
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const token = await getToken();
        const user = await apiRequest("/api/auth/clerk/session", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (cancelled) return;
        saveClerkAuth(token, user);
        const destination = user.role === "admin" ? "/admin" : user.role === "mentor" ? "/mentor-workspace" : "/mentors";
        navigate(destination, { replace: true });
      } catch (sessionError) {
        if (cancelled) return;
        if (sessionError.message?.includes("Complete AlumniConnect account setup")) {
          navigate("/clerk-onboarding", { replace: true });
        } else {
          setError(sessionError.message || "Unable to finish signing in. Please try again.");
        }
      }
    })();
    return () => { cancelled = true; };
  }, [isLoaded, isSignedIn, getToken, navigate, attempt]);

  return <main className="auth-page" aria-live="polite">
    <section className="auth-panel">
      <p role="status">{error ? "We couldn't finish signing you in." : "Finishing sign-in…"}</p>
      {error && <>
        <p className="auth-error" role="alert">{error}</p>
        <button className="btn btn-primary" type="button" onClick={() => { setError(""); setAttempt((value) => value + 1); }}>Try again</button>
      </>}
    </section>
  </main>;
}

function ClerkSSOCallback() {
  const navigate = useNavigate();
  return <HandleSSOCallback
    navigateToApp={() => navigate("/auth/complete", { replace: true })}
    navigateToSignIn={() => navigate("/login", { replace: true })}
    navigateToSignUp={() => navigate("/clerk-onboarding", { replace: true })}
  />;
}

// Every page outside sign-in and registration shares one footer.
function WithFooter() {
  return <><Outlet /><SiteFooter /></>;
}

function ClerkLoginPage() {
  // Do not redirect just because Clerk restored an existing browser session.
  // Keep the login screen available so the user can choose a provider or
  // sign in with a different AlumniConnect account.
  return <LoginPage />;
}

function App() {
  const communityRoles = ["mentor", "mentee", "admin"];
  return <BrowserRouter>{import.meta.env.VITE_CLERK_PUBLISHABLE_KEY && <ClerkSessionBridge />}<SessionRoleSync /><Routes>
    <Route path="/login" element={import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ? <ClerkLoginPage /> : <LoginPage />} />
    <Route path="/register" element={<RegisterPage />} />
    <Route path="/verify-email" element={<VerifyEmailPage />} />
    <Route path="/reset-password" element={<ResetPasswordPage />} />
    <Route path="/sso-callback" element={<ClerkSSOCallback />} />
    <Route path="/clerk-onboarding" element={<ClerkOnboardingPage />} />
    <Route path="/auth/complete" element={<ClerkAuthComplete />} />
    <Route element={<WithFooter />}>
    <Route path="/" element={<LandingPage />} />
    <Route path="/knowledge" element={<KnowledgePage />} />
    <Route path="/directory" element={<ProtectedRoute allowedRoles={communityRoles}><DirectoryPage /></ProtectedRoute>} />
    <Route path="/mentors" element={<ProtectedRoute allowedRoles={["mentee"]}><MentorsPage /></ProtectedRoute>} />
    <Route path="/my-mentorships" element={<ProtectedRoute allowedRoles={["mentee"]}><MyMentorshipsPage /></ProtectedRoute>} />
    <Route path="/mentorships/:mentorshipId" element={<ProtectedRoute allowedRoles={communityRoles}><WorkspaceLayout /></ProtectedRoute>}>
      <Route index element={<OverviewTab />} />
      <Route path="sessions" element={<SessionsTab />} />
      <Route path="sessions/:sessionId" element={<SessionDetailPage />} />
      <Route path="notes" element={<NotesTab />} />
      <Route path="goals" element={<GoalsTab />} />
      <Route path="progress" element={<ProgressTab />} />
    </Route>
    <Route path="/mentor-workspace"element={<ProtectedRoute allowedRoles={["mentor"]}><MentorWorkspacePage /></ProtectedRoute>} />
    <Route path="/profile" element={<ProtectedRoute allowedRoles={communityRoles}><MyProfilePage /></ProtectedRoute>} />
    <Route path="/notifications" element={<ProtectedRoute allowedRoles={communityRoles}><NotificationsPage /></ProtectedRoute>} />
    <Route path="/chats" element={<ProtectedRoute allowedRoles={communityRoles}><ChatsPage /></ProtectedRoute>} />
    <Route path="/admin" element={<ProtectedRoute allowedRoles={["admin"]}><AdminDashboard /></ProtectedRoute>} />
    <Route path="/mentor-profile/:mentorId" element={<ProtectedRoute allowedRoles={["mentee"]}><MentorProfilePage /></ProtectedRoute>} />
    <Route path="/admin-knowledge" element={<ProtectedRoute allowedRoles={["admin"]}><AdminKnowledgePage /></ProtectedRoute>} />
    <Route path="/admin/community" element={<ProtectedRoute allowedRoles={["admin"]}><AdminCommunityPage /></ProtectedRoute>} />
    <Route path="/admin-announcements" element={<ProtectedRoute allowedRoles={["admin"]}><AdminAnnouncementsPage /></ProtectedRoute>} />
    <Route path="/admin/users" element={<ProtectedRoute allowedRoles={["admin"]}><AdminUsersPage /></ProtectedRoute>} />
    <Route path="/admin/operations" element={<ProtectedRoute allowedRoles={["admin"]}><AdminOperationsPage /></ProtectedRoute>} />
    <Route path="/availability" element={<ProtectedRoute allowedRoles={["mentor"]}><AvailabilityPage /></ProtectedRoute>} />
    <Route path="/booking" element={<ProtectedRoute allowedRoles={communityRoles}><BookingPage /></ProtectedRoute>} />
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes></BrowserRouter>;
}

export default App;
