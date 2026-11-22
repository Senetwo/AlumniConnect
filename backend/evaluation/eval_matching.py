"""Evaluate mentor-matching rankings against the hand-labelled set in matching_dataset.py.

Run from the backend folder:

    .venv\\Scripts\\python.exe -m evaluation.eval_matching [--model PATH] [--base-model NAME]

Compares, per mentee query, a random ranking, a TF-IDF keyword baseline, and the sentence
embedding model(s) using the same profile-text format as production
(app.ml.profile_text_service). Two query variants are scored:
  full - domain, path, skills and goals are given
  cold - only skills and goals are given (no domain or path words to match on)

Writes JSON and Markdown to ../docs/evidence/.
"""
import argparse
import json
import math
import random
import re
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from app.ml.profile_text_service import profile_text_service
from evaluation.matching_dataset import MENTEES, MENTORS

BACKEND_DIR = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = BACKEND_DIR.parent / "docs" / "evidence"
SEED = 42


def profile(domain, path, skills, goals):
    return SimpleNamespace(
        career_domain=domain,
        career_path=path,
        experience="5 years",
        skills=skills,
        career_goals=goals,
        availability="Weekends",
    )


def tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower())


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


def metrics(ranked_relevance, n_relevant):
    """ranked_relevance: list of 0/1 in ranked order."""
    first = next((i for i, r in enumerate(ranked_relevance) if r), None)
    return {
        "p@1": ranked_relevance[0],
        "p@3": sum(ranked_relevance[:3]) / 3,
        "recall@3": sum(ranked_relevance[:3]) / n_relevant,
        "mrr": 1 / (first + 1) if first is not None else 0.0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=str(BACKEND_DIR / "ml_models" / "alumniconnect_sbert_finetuned"))
    parser.add_argument("--base-model", default="sentence-transformers/all-MiniLM-L6-v2")
    args = parser.parse_args()

    mentors = [(area, profile(*m)) for area, ms in MENTORS.items() for m in ms]
    mentor_areas = [a for a, _ in mentors]
    mentor_texts = [profile_text_service.create_profile_text(p) for _, p in mentors]

    rng = random.Random(SEED)
    systems = {
        "random": lambda q, d: [rng.random() for _ in d],
        "tfidf-keyword": tfidf_scores,
    }
    skipped = {}
    for name, path in (("base-minilm", args.base_model), ("fine-tuned", args.model)):
        try:
            systems[name] = embedding_scorer(path)
        except Exception as exc:  # model missing or no network for the base model
            skipped[name] = f"{type(exc).__name__}: {exc}"[:200]

    results = {}
    for variant in ("full", "cold"):
        queries = []
        for area, mentees in MENTEES.items():
            for domain, path, skills, goals in mentees:
                p = profile("", "", skills, goals) if variant == "cold" else profile(domain, path, skills, goals)
                if variant == "cold":
                    text = f"Skills: {skills}. Career goals: {goals}."
                else:
                    text = profile_text_service.create_profile_text(p)
                queries.append((area, text))
        for system, scorer in systems.items():
            per_query = []
            for area, text in queries:
                scores = scorer(text, mentor_texts)
                order = np.argsort(-np.array(scores), kind="stable")
                rel = [1 if mentor_areas[i] == area else 0 for i in order]
                per_query.append(metrics(rel, n_relevant=mentor_areas.count(area)))
            results.setdefault(variant, {})[system] = {
                k: round(float(np.mean([m[k] for m in per_query])), 3) for k in per_query[0]
            }

    meta = {
        "n_mentors": len(mentors),
        "n_queries": sum(len(v) for v in MENTEES.values()),
        "relevance": "binary: mentor in same career area as mentee",
        "seed": SEED,
        "fine_tuned_model_path": args.model,
        "base_model": args.base_model,
        "skipped_systems": skipped,
    }
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "matching_eval.json").write_text(json.dumps({"meta": meta, "results": results}, indent=2), encoding="utf-8")

    lines = [f"# Mentor matching evaluation ({meta['n_queries']} mentee queries, {meta['n_mentors']} mentors)", ""]
    for variant, label in (("full", "Full profiles (domain, path, skills, goals)"), ("cold", "Cold profiles (skills and goals only)")):
        lines += [f"## {label}", "", "| System | P@1 | P@3 | Recall@3 | MRR |", "|---|---|---|---|---|"]
        for system, m in results[variant].items():
            lines.append(f"| {system} | {m['p@1']} | {m['p@3']} | {m['recall@3']} | {m['mrr']} |")
        lines.append("")
    if skipped:
        lines += ["Skipped systems: " + "; ".join(f"{k} ({v})" for k, v in skipped.items()), ""]
    (EVIDENCE_DIR / "matching_eval.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
