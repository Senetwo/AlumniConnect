
import { Link } from "react-router-dom";
import Brand from "../components/Brand";

export default function Placeholder({ title }) {
  return (
    <div className="simple-page">
      <div className="simple-card">
        <Brand />

        <h1>{title}</h1>

        <p>This module is coming next.</p>

        <Link to="/" className="btn btn-primary">
          Back home
        </Link>
      </div>
    </div>
  );
}
