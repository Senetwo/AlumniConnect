import { Link } from "react-router-dom";
import KenyaAirwaysRoundel from "./KenyaAirwaysRoundel";

// Single source of truth for the AlumniConnect identity: the Kenya Airways
// roundel followed by the product name. `inverse` is for dark surfaces; `to`
// and `onClick` let the navbar reuse it for admin/home.
export default function Brand({ to = "/", inverse = false, className = "", onClick }) {
  return (
    <Link
      to={to}
      onClick={onClick}
      className={`brand ${inverse ? "brand-inverse" : ""} ${className}`.trim()}
      aria-label="AlumniConnect home"
    >
      <KenyaAirwaysRoundel className="brand-roundel" size={38} fill={inverse ? "#FFFFFF" : undefined} />
      <span className="brand-name">AlumniConnect</span>
    </Link>
  );
}
