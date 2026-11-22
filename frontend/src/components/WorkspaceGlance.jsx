import { AlertCircle, CalendarClock, ListChecks } from "lucide-react";
import { formatEventDate } from "../utils/format";

// One line on a mentorship card: what is open, what is late, and when the next session is.
export default function WorkspaceGlance({ info }) {
  return (
    <ul className="ws-glance" aria-label="Mentorship at a glance">
      <li><ListChecks size={15} aria-hidden="true" />{info.open_action_items} open action item{info.open_action_items === 1 ? "" : "s"}</li>
      {info.overdue_action_items > 0 && <li className="is-late"><AlertCircle size={15} aria-hidden="true" />{info.overdue_action_items} overdue</li>}
      <li><CalendarClock size={15} aria-hidden="true" />{info.next_session ? `Next session ${formatEventDate(info.next_session.scheduled_at).full} EAT` : "No session scheduled"}</li>
    </ul>
  );
}
