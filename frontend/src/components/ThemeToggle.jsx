import { useState } from "react";
import { Moon, Sun } from "lucide-react";

const KEY = "alumniconnect_theme";

// The theme is set on <html data-theme> before first paint by a script in index.html.
export default function ThemeToggle({ floating = false, withLabel = false }) {
  const [theme, setTheme] = useState(() => document.documentElement.dataset.theme || "light");
  const dark = theme === "dark";

  function toggle() {
    const next = dark ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem(KEY, next); } catch { /* storage can be blocked; the choice still applies this visit */ }
    setTheme(next);
  }

  return (
    <button
      type="button"
      className={`theme-toggle ${floating ? "is-floating" : ""} ${withLabel ? "has-label" : ""}`}
      onClick={toggle}
      aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
      title={dark ? "Light mode" : "Dark mode"}
    >
      {dark ? <Sun size={withLabel ? 17 : 18} aria-hidden="true" /> : <Moon size={withLabel ? 17 : 18} aria-hidden="true" />}
      {withLabel && (dark ? "Light mode" : "Dark mode")}
    </button>
  );
}
