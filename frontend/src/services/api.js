
import { clearAuth, getRequestToken } from "./authStorage";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function apiRequest(path, options = {}) {
  const token = await getRequestToken();

  const headers = {
    ...(options.body && !(options.body instanceof FormData)
      ? { "Content-Type": "application/json" }
      : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = data?.detail;
    // An out-of-date sign-in cannot recover on its own: clear it and return to the login page.
    if (response.status === 401 && token && typeof detail === "string" && detail.includes("session has expired")) {
      clearAuth();
      if (window.location.pathname !== "/login") window.location.assign("/login");
    }
    const message =
      typeof detail === "string"
        ? detail
        : response.status === 401
          ? "Your session may have expired. Please sign in again."
          : response.status === 403
            ? "You do not have permission to perform this request."
            : `Request failed (${response.status}). Please try again.`;

    throw new Error(message);
  }

  return data;
}
