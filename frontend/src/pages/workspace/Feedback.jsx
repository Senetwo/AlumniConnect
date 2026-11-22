import { useCallback, useEffect, useState } from "react";
import { Star } from "lucide-react";
import { apiRequest } from "../../services/api";

// Shown on a completed mentorship. Only the person who answers can see their own answer.
export default function Feedback({ base }) {
  const [state, setState] = useState(null);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try { setState(await apiRequest(`${base}/feedback`)); } catch (err) { setError(err.message || "Could not load feedback."); }
  }, [base]);
  useEffect(() => { queueMicrotask(() => { void load(); }); }, [load]);

  async function submit(event) {
    event.preventDefault();
    if (!rating) { setError("Choose a rating from 1 to 5."); return; }
    setBusy(true); setError("");
    try { await apiRequest(`${base}/feedback`, { method: "POST", body: JSON.stringify({ rating, comment }) }); await load(); }
    catch (err) { setError(err.message || "Could not save your feedback."); }
    finally { setBusy(false); }
  }

  if (!state) return error ? <div className="page-alert" role="alert">{error}</div> : null;
  if (state.mine) {
    return <section className="pg-card ws-feedback" aria-label="Your feedback"><h2>Thank you for your feedback</h2><p className="ws-muted">You rated how well this match worked: {state.mine.rating} out of 5. Only you and the programme administrators can see this.</p></section>;
  }
  if (!state.can_submit) return null;
  return (
    <section className="pg-card ws-feedback" aria-label="Rate this match">
      <h2>How well did this match work for you?</h2>
      <p className="ws-muted">Your answer helps improve mentor recommendations. The other person will not see it.</p>
      <form onSubmit={submit}>
        {error && <div className="page-alert" role="alert">{error}</div>}
        <fieldset className="ws-stars">
          <legend className="visually-hidden">Rating from 1 to 5</legend>
          {[1, 2, 3, 4, 5].map((value) => (
            <label key={value} className={value <= rating ? "is-on" : ""} title={`${value} out of 5`}>
              <input type="radio" name="rating" value={value} checked={rating === value} onChange={() => setRating(value)} />
              <Star size={26} aria-hidden="true" /><span className="visually-hidden">{value} out of 5</span>
            </label>
          ))}
        </fieldset>
        <div className="register-field">
          <label htmlFor="fb-comment">Anything to add? (optional)</label>
          <textarea id="fb-comment" rows={3} maxLength={1000} value={comment} onChange={(event) => setComment(event.target.value)} />
        </div>
        <button className="btn btn-primary" disabled={busy}>{busy ? "Sending…" : "Send feedback"}</button>
      </form>
    </section>
  );
}
