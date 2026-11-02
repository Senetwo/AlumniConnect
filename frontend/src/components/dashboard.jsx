import { formatEventDate } from "../utils/format";

export function PageHeader({ eyebrow, title, subtitle, actions }) {
  return (
    <header className="pg-header">
      <div>
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {actions && <div className="pg-header-actions">{actions}</div>}
    </header>
  );
}

export function StatCard({ icon: Icon, label, value, hint, tone }) {
  return (
    <article className={`pg-card pg-stat ${tone ? `is-${tone}` : ""}`}>
      {Icon && <span className="pg-stat-icon" aria-hidden="true"><Icon size={20} /></span>}
      <div>
        <strong>{value}</strong>
        <span>{label}</span>
        {hint && <small>{hint}</small>}
      </div>
    </article>
  );
}

export function FilterTabs({ label, options, value, onChange }) {
  return (
    <div className="pg-tabs" role="group" aria-label={label}>
      {options.map((option) => (
        <button key={option.id} type="button" aria-pressed={value === option.id} className={value === option.id ? "is-active" : ""} onClick={() => onChange(option.id)}>
          {option.label}
          {option.count !== undefined && <span>{option.count}</span>}
        </button>
      ))}
    </div>
  );
}

// Month and day tile, the same one the community events use.
export function DateTile({ iso }) {
  const date = formatEventDate(iso);
  return <div className="pg-date" aria-hidden="true"><span>{date.month}</span><strong>{date.day}</strong></div>;
}
