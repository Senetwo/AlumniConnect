import { useEffect, useId, useRef } from "react";
import { X } from "lucide-react";
import { label } from "./format";

export function StatusChip({ value, children }) {
  return <span className={`ws-chip is-${value}`}>{children ?? label(value)}</span>;
}

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function Modal({ title, onClose, children, wide = false }) {
  const ref = useRef(null);
  const titleId = useId();
  useEffect(() => {
    const opener = document.activeElement;
    const onKey = (event) => {
      if (event.key === "Escape") { onClose(); return; }
      if (event.key !== "Tab" || !ref.current) return;
      const items = [...ref.current.querySelectorAll(FOCUSABLE)];
      if (!items.length) return;
      const first = items[0], last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", onKey);
    (ref.current?.querySelector("input, select, textarea") ?? ref.current?.querySelector("button"))?.focus();
    return () => { document.removeEventListener("keydown", onKey); opener?.focus?.(); };
  }, [onClose]);
  return (
    <div className="ws-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <div className={`ws-modal ${wide ? "is-wide" : ""}`} role="dialog" aria-modal="true" aria-labelledby={titleId} ref={ref}>
        <header><h2 id={titleId}>{title}</h2><button type="button" className="ws-icon-button" onClick={onClose} aria-label="Close"><X size={18} aria-hidden="true" /></button></header>
        {children}
      </div>
    </div>
  );
}

export function ConfirmDialog({ title, message, confirmLabel, danger = false, busy, onConfirm, onClose, children }) {
  return (
    <Modal title={title} onClose={onClose}>
      <p className="ws-muted">{message}</p>
      {children}
      <div className="ws-form-actions">
        <button type="button" className="btn btn-outline" onClick={onClose} disabled={busy}>Keep as is</button>
        <button type="button" className={`btn ${danger ? "btn-danger" : "btn-primary"}`} onClick={onConfirm} disabled={busy}>{busy ? "Saving…" : confirmLabel}</button>
      </div>
    </Modal>
  );
}

export function Empty({ icon: Icon, title, children, action }) {
  return (
    <div className="pg-card pg-empty">
      {Icon && <Icon size={28} aria-hidden="true" />}
      <h3>{title}</h3>
      {children && <p>{children}</p>}
      {action}
    </div>
  );
}

export function Loading({ text = "Loading" }) {
  return <div className="pg-card pg-skeleton" role="status" aria-label={text} />;
}

export function Field({ id, label: text, hint, children }) {
  return (
    <div className="register-field">
      <label htmlFor={id}>{text}</label>
      {children}
      {hint && <small className="ws-hint">{hint}</small>}
    </div>
  );
}
