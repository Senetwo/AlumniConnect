"""Evaluate retrieval for "Ask the library" on the synthetic set in rag_dataset.py.

Run from the backend folder:

    .venv\\Scripts\\python.exe -m evaluation.eval_rag [--model PATH] [--base-model NAME]

Retrieval only: no language-model calls are made, so it costs nothing. Systems compared:
  substring     the current Knowledge page search (the whole question must appear in the text)
  tfidf-keyword TF-IDF cosine over title and description
  base-minilm / fine-tuned   sentence embeddings, as used in production
Also measures whether out-of-library questions fall below the similarity floor
(settings.rag_min_similarity) so the assistant would decline without calling the model.

Writes JSON and Markdown to ../docs/evidence/.
"""
import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path

from evaluation.rag_dataset import DOCUMENTS, OUT_OF_LIBRARY, QUESTIONS

BACKEND_DIR = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = BACKEND_DIR.parent / "docs" / "evidence"
DEFAULT_FLOOR = 0.25


def tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def substring_scores(query, docs):
    """What the existing ilike search does with a whole question: match only if it appears verbatim."""
    needle = query.strip().lower()
    return [1.0 if needle in doc.lower() else 0.0 for doc in docs]


def tfidf_scores(query, docs):
    doc_tokens = [tokens(d) for d in docs]
    n = len(docs)
    df = Counter(t for d in doc_tokens for t in set(d))
    idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}

    def vec(toks):
        tf = Counter(toks)
        return {t: tf[t] * idf.get(t, 0.0) for t in tf}

    def cos(a, b):
        dot = sum(a[t] * b.get(t, 0.0) for t in a)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        return dot / (na * nb) if na and nb else 0.0

    q = vec(tokens(query))
    return [cos(q, vec(d)) for d in doc_tokens]


def embedding_scorer(model_name_or_path):
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(str(model_name_or_path))

    def score(query, docs):
        vecs = model.encode([query] + docs, normalize_embeddings=True)
        return (vecs[1:] @ vecs[0]).tolist()

    return score


def rank_of(scores, gold):
    """1-based rank of the gold document; ties are broken against the system (worst case)."""
    better_or_equal = sum(1 for i, s in enumerate(scores) if i != gold and s >= scores[gold])
    return better_or_equal + 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=str(BACKEND_DIR / "ml_models" / "alumniconnect_sbert_finetuned"))
    parser.add_argument("--base-model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--floor", type=float, default=DEFAULT_FLOOR)
    args = parser.parse_args()

    docs = [f"{title}. {text}" for title, text in DOCUMENTS]
    systems = {"substring": substring_scores, "tfidf-keyword": tfidf_scores}
    skipped = {}
    for name, path in (("base-minilm", args.base_model), ("fine-tuned", args.model)):
        try:
            systems[name] = embedding_scorer(path)
        except Exception as exc:
            skipped[name] = f"{type(exc).__name__}: {exc}"[:200]

    results = {}
    for name, scorer in systems.items():
        ranks, gold_scores, out_top = [], [], []
        for question, gold in QUESTIONS:
            scores = scorer(question, docs)
            ranks.append(rank_of(scores, gold))
            gold_scores.append(scores[gold])
        for question in OUT_OF_LIBRARY:
            out_top.append(max(scorer(question, docs)))
        n = len(QUESTIONS)
        results[name] = {
            "hit@1": sum(r <= 1 for r in ranks) / n,
            "hit@3": sum(r <= 3 for r in ranks) / n,
            "mrr": sum(1 / r for r in ranks) / n,
            "answerable_above_floor": sum(s >= args.floor for s in gold_scores) / n,
            "declined_out_of_library": sum(s < args.floor for s in out_top) / len(OUT_OF_LIBRARY),
            "min_gold_score": round(min(gold_scores), 3),
            "max_out_of_library_score": round(max(out_top), 3),
        }

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "rag_eval.json").write_text(
        json.dumps({"floor": args.floor, "skipped": skipped, "results": results}, indent=2), encoding="utf-8"
    )

    lines = [
        f"# Ask-the-library retrieval evaluation ({len(QUESTIONS)} answerable and {len(OUT_OF_LIBRARY)} out-of-library questions, {len(DOCUMENTS)} documents)",
        "",
        f"Similarity floor for the embedding systems: {args.floor}. The substring and TF-IDF scores are not on the same scale, so the last two columns apply only to the embedding systems.",
        "",
        "| System | Hit@1 | Hit@3 | MRR | Answerable questions above floor | Out-of-library declined |",
        "|---|---|---|---|---|---|",
    ]
    for name, r in results.items():
        embed = name in ("base-minilm", "fine-tuned")
        lines.append(
            f"| {name} | {r['hit@1']:.3f} | {r['hit@3']:.3f} | {r['mrr']:.3f} | "
            f"{r['answerable_above_floor']:.3f}" if embed else f"| {name} | {r['hit@1']:.3f} | {r['hit@3']:.3f} | {r['mrr']:.3f} | n/a"
        )
        lines[-1] += f" | {r['declined_out_of_library']:.3f} |" if embed else " | n/a |"
    lines += ["", "Lowest similarity of a correct document and highest similarity of an out-of-library question (embedding systems):", ""]
    for name, r in results.items():
        if name in ("base-minilm", "fine-tuned"):
            lines.append(f"- {name}: lowest correct {r['min_gold_score']}, highest out-of-library {r['max_out_of_library_score']}")
    for name, reason in skipped.items():
        lines.append(f"- {name} skipped: {reason}")
    (EVIDENCE_DIR / "rag_eval.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
