// Date and text helpers for the mentorship workspace.
const asDate = (iso) => new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`);

// Sessions are scheduled in East Africa Time, the same zone the rest of the app uses.
export function formatWhen(iso) {
  const date = asDate(iso);
  const eat = date.toLocaleString("en-KE", {
    weekday: "short", day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "Africa/Nairobi",
  }) + " EAT";
  // Show the viewer's own time as well when they are not in East Africa.
  if (-date.getTimezoneOffset() === 180) return eat;
  const local = date.toLocaleString([], { weekday: "short", hour: "2-digit", minute: "2-digit" });
  return `${eat} (your time: ${local})`;
}

export const formatDate = (value) => value
  ? new Date(value.length === 10 ? `${value}T00:00:00` : value).toLocaleDateString("en-KE", { day: "numeric", month: "short", year: "numeric" })
  : "";

// <input type="datetime-local"> value for an ISO timestamp, expressed in EAT.
export function toEatInput(iso) {
  const parts = new Intl.DateTimeFormat("sv-SE", {
    timeZone: "Africa/Nairobi", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23",
  }).format(asDate(iso));
  return parts.replace(" ", "T");
}

export const fromEatInput = (local) => `${local}:00+03:00`;

export const label = (value = "") => {
  const text = value.replaceAll("_", " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
};

export const NOTE_SECTIONS = [
  ["topics_discussed", "Topics discussed"],
  ["key_takeaways", "Key takeaways"],
  ["challenges", "Challenges encountered"],
  ["advice", "Advice and recommendations"],
  ["decisions", "Decisions made"],
  ["next_steps", "Next steps"],
];
