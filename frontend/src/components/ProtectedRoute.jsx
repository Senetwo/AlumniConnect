
import { Navigate } from "react-router-dom";
import { getAuth } from "../services/authStorage";

export default function ProtectedRoute({ children, allowedRoles }) {
  const auth = getAuth();

  if (!auth) {
    return <Navigate to="/login" replace />;
  }

  const roleAllowed = allowedRoles?.includes(auth.user.role)
    || (auth.user.role === "admin" && allowedRoles?.includes(auth.user.community_role));

  if (allowedRoles && !roleAllowed) {
    return <Navigate to="/" replace />;
  }

  return children;
}
