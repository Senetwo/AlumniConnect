import { Link, useLocation } from "react-router-dom";
import Brand from "./Brand";
import { getAuth } from "../services/authStorage";
import kenyaAirwaysLogoWhite from "../assets/brand/kenya-airways-logo-white.svg";

// One footer for every page. Its links follow who is signed in.
export default function SiteFooter() {
  const { pathname } = useLocation();
  const user = getAuth()?.user;
  const role = user?.community_role || user?.role;
  const onLanding = pathname === "/";

  return (
    <footer className="lp-footer">
      <div className="lp-footer-inner">
        <div className="lp-footer-brand">
          <Brand inverse />
          <p>A community built on experience, opportunity, and connection.</p>
        </div>

        <nav aria-label="Explore">
          <h2>Explore</h2>
          {onLanding && !user ? (
            <>
              <a href="#about">About</a>
              <a href="#features">Features</a>
              <a href="#how-it-works">How it works</a>
            </>
          ) : user && user.role !== "admin" ? (
            <>
              <Link to="/directory">Community</Link>
              {role === "mentor"
                ? <><Link to="/mentor-workspace">My dashboard</Link><Link to="/availability">Availability</Link></>
                : <><Link to="/mentors">Discover mentors</Link><Link to="/my-mentorships">My mentorships</Link></>}
              <Link to="/booking">Bookings</Link>
            </>
          ) : (
            <Link to="/">Home</Link>
          )}
          <Link to="/knowledge">Knowledge Hub</Link>
        </nav>

        <nav aria-label="Account">
          <h2>Account</h2>
          {user ? (
            <>
              {user.role !== "admin" && <Link to="/profile">My profile</Link>}
              <Link to="/notifications">Notifications</Link>
              {user.role !== "admin" && <Link to="/chats">Messages</Link>}
            </>
          ) : (
            <>
              <Link to="/login">Sign in</Link>
              <Link to="/register">Create account</Link>
            </>
          )}
        </nav>
      </div>

      <div className="lp-footer-bar">
        <span>© {new Date().getFullYear()} AlumniConnect</span>
        <img src={kenyaAirwaysLogoWhite} alt="Kenya Airways" />
      </div>
    </footer>
  );
}
