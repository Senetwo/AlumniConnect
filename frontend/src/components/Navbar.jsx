import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Bell,
  BookOpen,
  CalendarClock,
  CalendarDays,
  Compass,
  Handshake,
  ChevronDown,
  LayoutDashboard,
  LogOut,
  Menu,
  Megaphone,
  MessageCircle,
  ShieldCheck,
  UserRound,
  Users,
  X,
} from "lucide-react";
import { getAuth, signOutCurrentUser } from "../services/authStorage";
import Brand from "./Brand";
import ThemeToggle from "./ThemeToggle";

export default function Navbar({ landing = false }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [unreadNotifications, setUnreadNotifications] = useState(0);
  const [unreadMessages, setUnreadMessages] = useState(0);
  const location = useLocation();
  const contentMenuRef = useRef(null);
  const auth = getAuth();
  const user = auth?.user;
  const isAuthenticated = Boolean(auth);
  const isAdmin = user?.role === "admin" && !landing;
  const communityRole = user?.community_role || (user?.role === "admin" ? null : user?.role);
  const isMentor = communityRole === "mentor";
  const isMentee = communityRole === "mentee";

  const closeMenu = () => setMenuOpen(false);
  // A mentorship workspace (/mentorships/:id/...) belongs to "My mentorships" / "Dashboard".
  const inWorkspace = location.pathname.startsWith("/mentorships/");
  const navLink = (to, label, className = "") => {
    const active = location.pathname === to || (inWorkspace && (to === "/my-mentorships" || to === "/mentor-workspace"));
    return (
    <Link
      key={`${to}-${label}`}
      to={to}
      onClick={closeMenu}
      className={`${className} ${active ? "is-active" : ""}`.trim()}
      aria-current={active ? "page" : undefined}
    >
      {label}
    </Link>
    );
  };

  useEffect(() => {
    const token = getAuth()?.token;
    if (!token) return undefined;
    let active = true;
    const headers = { Authorization: `Bearer ${token}` };

    async function loadUnreadCounts() {
      try {
        const [notificationsResponse, messagesResponse] = await Promise.all([
          fetch("http://127.0.0.1:8000/api/notifications/unread-count", { headers }),
          fetch("http://127.0.0.1:8000/api/chat/unread-count", { headers }),
        ]);
        if (!notificationsResponse.ok || !messagesResponse.ok) return;
        const [notifications, messages] = await Promise.all([
          notificationsResponse.json(),
          messagesResponse.json(),
        ]);
        if (active) {
          setUnreadNotifications(notifications.count ?? 0);
          setUnreadMessages(messages.count ?? 0);
        }
      } catch (error) {
        console.error("Unable to refresh unread counts:", error);
      }
    }

    void loadUnreadCounts();
    const interval = window.setInterval(loadUnreadCounts, 30000);
    window.addEventListener("alumniconnect:notifications-updated", loadUnreadCounts);
    return () => {
      active = false;
      window.clearInterval(interval);
      window.removeEventListener("alumniconnect:notifications-updated", loadUnreadCounts);
    };
  }, []);

  useEffect(() => {
    contentMenuRef.current?.removeAttribute("open");
  }, [location.pathname]);

  useEffect(() => {
    const closeOnOutside = (event) => {
      const menu = contentMenuRef.current;
      if (menu?.open && !menu.contains(event.target)) menu.removeAttribute("open");
    };
    const closeOnEscape = (event) => {
      if (event.key === "Escape") contentMenuRef.current?.removeAttribute("open");
    };
    document.addEventListener("pointerdown", closeOnOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("pointerdown", closeOnOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, []);

  const handleLogout = async () => {
    await signOutCurrentUser();
    closeMenu();
    window.location.href = "/";
  };

  const utilityLinks = (
    <>
      <Link to="/notifications" onClick={closeMenu} className="nav-icon-link" aria-label={`Notifications${unreadNotifications ? `, ${unreadNotifications} unread` : ""}`} title="Notifications">
        <span className="nav-badge-anchor"><Bell size={19} />{unreadNotifications > 0 && <span className="nav-count-badge">{unreadNotifications > 99 ? "99+" : unreadNotifications}</span>}</span>
      </Link>
      <Link to="/chats" onClick={closeMenu} className="nav-icon-link" aria-label={`Chats${unreadMessages ? `, ${unreadMessages} unread` : ""}`} title="Chats">
        <span className="nav-badge-anchor"><MessageCircle size={19} />{unreadMessages > 0 && <span className="nav-count-badge">{unreadMessages > 99 ? "99+" : unreadMessages}</span>}</span>
      </Link>
      <Link to="/profile" onClick={closeMenu} className="nav-icon-link" aria-label="My profile" title="My profile">
        <span className="nav-avatar-mark">{user?.full_name?.trim()?.[0]?.toUpperCase() || "U"}</span>
      </Link>
    </>
  );

  const mobileUtilityLinks = (
    <>
      <Link to="/notifications" onClick={closeMenu} className="mobile-icon-row"><Bell size={17} aria-hidden="true" />Notifications{unreadNotifications > 0 && <span className="mobile-count">{unreadNotifications > 99 ? "99+" : unreadNotifications}</span>}</Link>
      <Link to="/chats" onClick={closeMenu} className="mobile-icon-row"><MessageCircle size={17} aria-hidden="true" />Messages{unreadMessages > 0 && <span className="mobile-count">{unreadMessages > 99 ? "99+" : unreadMessages}</span>}</Link>
      <Link to="/profile" onClick={closeMenu} className="mobile-icon-row"><UserRound size={17} aria-hidden="true" />My profile</Link>
      <ThemeToggle withLabel />
    </>
  );

  const row = (to, label, Icon) => navLink(to, <><Icon size={17} aria-hidden="true" />{label}</>, "mobile-icon-row");
  const mobileCommunityLinks = (
    <>
      {row("/directory", "Community", Users)}
      {isMentee && <>{row("/mentors", "Discover mentors", Compass)}{row("/my-mentorships", "My mentorships", Handshake)}{row("/booking", "Bookings", CalendarClock)}</>}
      {isMentor && <>{row("/mentor-workspace", "Dashboard", LayoutDashboard)}{row("/availability", "Availability", CalendarDays)}{row("/booking", "Bookings", CalendarClock)}</>}
      {row("/knowledge", "Knowledge Hub", BookOpen)}
    </>
  );

  const communityLinks = (
    <>
      {navLink("/directory", "Community")}
      {isMentee && <>{navLink("/mentors", "Discover mentors")}{navLink("/my-mentorships", "My mentorships")}{navLink("/booking", "Bookings")}</>}
      {isMentor && <>{navLink("/mentor-workspace", "Dashboard")}{navLink("/availability", "Availability")}{navLink("/booking", "Bookings")}</>}
      {navLink("/knowledge", "Knowledge Hub")}
    </>
  );

  const adminLinks = (
    <>
      {navLink("/admin", <><LayoutDashboard size={16} />Overview</>, "admin-nav-link")}
      {navLink("/admin/users", <><Users size={16} />Members</>, "admin-nav-link")}
      {navLink("/admin/operations", <><ShieldCheck size={16} />Operations</>, "admin-nav-link")}
      <details ref={contentMenuRef} className={`admin-nav-menu ${["/admin-knowledge", "/admin-announcements", "/admin/community"].includes(location.pathname) ? "is-active" : ""}`}>
        <summary><BookOpen size={16} />Content<ChevronDown size={14} /></summary>
        <div className="admin-nav-dropdown">
          {navLink("/admin-knowledge", <><BookOpen size={16} aria-hidden="true" />Knowledge Hub</>)}
          {navLink("/admin-announcements", <><Megaphone size={16} aria-hidden="true" />Announcements</>)}
          {navLink("/admin/community", <><CalendarDays size={16} aria-hidden="true" />Events &amp; jobs</>)}
        </div>
      </details>
    </>
  );

  return (
    <header className={`navbar navbar-main ${isAdmin ? "navbar-admin" : ""}`}>
      <Brand to={isAdmin ? "/admin" : "/"} onClick={closeMenu} />

      <nav className={`nav-links ${isAdmin ? "admin-nav-links" : ""}`} aria-label={isAdmin ? "Admin navigation" : "Main navigation"}>
        {isAdmin ? adminLinks : <>
          {!landing && navLink("/", "Home")}
          {landing && <><a href="#about">About</a><a href="#features">Features</a><a href="#how-it-works">How it works</a>{navLink("/knowledge", "Knowledge Hub")}</>}
          {landing && isAuthenticated && user?.role === "admin" && navLink("/admin", "Admin Console")}
          {landing && isAuthenticated && (isMentor || isMentee || user?.role === "admin") && navLink("/directory", "Community")}
          {!landing && isAuthenticated && communityLinks}
          {!landing && !isAuthenticated && navLink("/knowledge", "Knowledge Hub")}
        </>}
      </nav>

      <div className="nav-actions">
        <ThemeToggle />
        {!isAuthenticated ? <>
          <Link to="/login" className="btn btn-outline">Log in</Link>
          <Link to="/register" className="btn btn-primary">{landing ? "Join the community" : "Get started"}</Link>
        </> : isAdmin ? <>
          {navLink("/directory", "Community", "workspace-switch-link")}
          {utilityLinks}
          <button type="button" className="nav-logout-button" onClick={handleLogout}><LogOut size={17} aria-hidden="true" /><span>Log out</span></button>
        </> : <>
          {utilityLinks}
          <button type="button" className="nav-logout-button" onClick={handleLogout}><LogOut size={17} aria-hidden="true" /><span>Log out</span></button>
        </>}
      </div>

      <button type="button" className="mobile-menu-button" onClick={() => setMenuOpen(!menuOpen)} aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"} aria-expanded={menuOpen}>
        {menuOpen ? <X size={22} /> : <Menu size={22} />}
      </button>

      {menuOpen && <div className={`mobile-nav ${isAdmin ? "admin-mobile-nav" : ""}`}>
        {landing && <><a href="#about" onClick={closeMenu}>About</a><a href="#features" onClick={closeMenu}>Features</a><a href="#how-it-works" onClick={closeMenu}>How it works</a>{navLink("/knowledge", "Knowledge Hub")}</>}
        {isAdmin ? <>
          <div className="mobile-nav-caption">ADMIN CONSOLE</div>
          {navLink("/admin", <><LayoutDashboard size={17} />Overview</>)}
          {navLink("/admin/users", <><Users size={17} />Members</>)}
          {navLink("/admin/operations", <><ShieldCheck size={17} />Operations</>)}
          {navLink("/admin-knowledge", <><BookOpen size={17} />Knowledge Hub</>)}
          {navLink("/admin-announcements", <><Bell size={17} />Announcements</>)}
          {navLink("/admin/community", <><CalendarDays size={17} />Events &amp; jobs</>)}
          <div className="mobile-nav-divider" />
          {navLink("/directory", "Switch to Community", "mobile-workspace-link")}
          {mobileUtilityLinks}
          <button type="button" className="mobile-nav-logout" onClick={handleLogout}><LogOut size={17} />Log out</button>
        </> : isAuthenticated ? <>
          {landing && (isMentor || isMentee || user?.role === "admin") && navLink("/directory", "Member Directory")}
          {landing && user?.role === "admin" && navLink("/admin", "Admin Console")}
          {mobileCommunityLinks}
          <div className="mobile-nav-divider" />
          {mobileUtilityLinks}
          <button type="button" className="mobile-nav-logout" onClick={handleLogout}><LogOut size={17} aria-hidden="true" />Log out</button>
        </> : <>
          {navLink("/knowledge", "Knowledge Hub")}
          <div className="mobile-nav-actions"><Link to="/login" className="btn btn-outline" onClick={closeMenu}>Log in</Link><Link to="/register" className="btn btn-primary" onClick={closeMenu}>{landing ? "Join the community" : "Get started"}</Link></div>
        </>}
      </div>}
    </header>
  );
}
