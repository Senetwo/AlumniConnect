import { useState } from "react";
import { apiRequest } from "../../services/api";
import SessionForm from "./SessionForm";
import { ConfirmDialog } from "./ui";

// Edit, cancel and complete actions shared by the list and the detail page.
export function useSessionActions(base, onChanged) {
  const [editing, setEditing] = useState(null);
  const [cancelling, setCancelling] = useState(null);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function post(path, body) {
    setBusy(true); setError("");
    try { await apiRequest(`${base}${path}`, { method: "POST", body: JSON.stringify(body ?? {}) }); await onChanged(); }
    catch (err) { setError(err.message || "That did not work."); }
    finally { setBusy(false); setCancelling(null); setReason(""); }
  }

  const dialogs = (
    <>
      {editing && <SessionForm base={base} session={editing} onClose={() => setEditing(null)} onSaved={async () => { setEditing(null); await onChanged(); }} />}
      {cancelling && (
        <ConfirmDialog
          title="Cancel this session?" message={`"${cancelling.title}" will be marked as cancelled and the other person will be told.${cancelling.from_booking ? " The booked time slot becomes available again." : ""}`}
          confirmLabel="Cancel session" danger busy={busy} onClose={() => setCancelling(null)}
          onConfirm={() => post(`/sessions/${cancelling.id}/cancel`, { reason })}
        >
          <div className="register-field">
            <label htmlFor="cancel-reason">Reason (optional)</label>
            <input id="cancel-reason" value={reason} maxLength={500} onChange={(event) => setReason(event.target.value)} />
          </div>
        </ConfirmDialog>
      )}
    </>
  );
  return { dialogs, error, onEdit: setEditing, onCancel: setCancelling, onComplete: (session) => post(`/sessions/${session.id}/complete`) };
}
