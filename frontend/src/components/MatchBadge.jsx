import { Sparkles, ThumbsUp } from "lucide-react";

export default function MatchBadge({ match }) {
  if (!match) return null;
  const Icon = match.tier === "best" ? Sparkles : ThumbsUp;
  return (
    <span className={`match-badge match-${match.tier}`} title="Ranked by how closely their experience, skills and goals fit your profile.">
      <Icon size={15} aria-hidden="true" />{match.label}
    </span>
  );
}
