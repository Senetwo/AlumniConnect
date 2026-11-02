// The API returns ISO timestamps; SQLite-backed environments may omit the offset.
const toDate = (iso) => new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`);

// Test accounts use Gmail plus-addressing (name+tag@gmail.com). Show the tag alone so the
// owner's own address is not exposed in the interface.
export function displayEmail(email = "") {
  const [local, domain] = email.split("@");
  const plus = local.indexOf("+");
  return domain && plus > 0 ? `${local.slice(plus + 1)}@${domain}` : email;
}

export const initials = (name = "") =>
  name.split(" ").filter(Boolean).map((part) => part[0]).join("").slice(0, 2).toUpperCase() || "?";

export function timeAgo(iso) {
  const seconds = Math.max(0, Math.round((Date.now() - toDate(iso).getTime()) / 1000));
  if (seconds < 60) return "Just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.round(hours / 24);
  if (days < 7) return `${days}d`;
  return toDate(iso).toLocaleDateString("en-KE", { day: "numeric", month: "short", year: "numeric" });
}

// Events and deadlines are shown in East Africa Time, the community's home zone.
export function formatEventDate(iso) {
  const date = toDate(iso);
  return {
    month: date.toLocaleString("en-KE", { month: "short", timeZone: "Africa/Nairobi" }).toUpperCase(),
    day: date.toLocaleString("en-KE", { day: "numeric", timeZone: "Africa/Nairobi" }),
    full: date.toLocaleString("en-KE", {
      weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "Africa/Nairobi",
    }),
  };
}

export const formatDay = (iso) =>
  toDate(iso).toLocaleDateString("en-KE", { day: "numeric", month: "short", year: "numeric", timeZone: "Africa/Nairobi" });
