// Turn similarity scores into a plain-language rank. Ranking is relative to the
// recommendations shown, so the raw score never appears in the interface.
export function matchLabels(mentors) {
  const scores = mentors.map((mentor) => Number(mentor.similarity_score)).filter(Number.isFinite);
  const best = Math.max(...scores);
  return Object.fromEntries(mentors.map((mentor) => {
    const score = Number(mentor.similarity_score);
    if (!Number.isFinite(score)) return [mentor.id, null];
    if (score === best) return [mentor.id, { tier: "best", label: "Best match" }];
    if (best - score <= 8) return [mentor.id, { tier: "strong", label: "Strong match" }];
    return [mentor.id, { tier: "good", label: "Good match" }];
  }));
}
