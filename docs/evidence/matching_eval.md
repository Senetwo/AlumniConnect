# Mentor matching evaluation (21 mentee queries, 14 mentors)

## Full profiles (domain, path, skills, goals)

| System | P@1 | P@3 | Recall@3 | MRR |
|---|---|---|---|---|
| random | 0.048 | 0.063 | 0.095 | 0.24 |
| tfidf-keyword | 1.0 | 0.667 | 1.0 | 1.0 |
| base-minilm | 1.0 | 0.667 | 1.0 | 1.0 |
| fine-tuned | 1.0 | 0.667 | 1.0 | 1.0 |

## Cold profiles (skills and goals only)

| System | P@1 | P@3 | Recall@3 | MRR |
|---|---|---|---|---|
| random | 0.19 | 0.143 | 0.214 | 0.376 |
| tfidf-keyword | 1.0 | 0.508 | 0.762 | 1.0 |
| base-minilm | 0.952 | 0.619 | 0.929 | 0.968 |
| fine-tuned | 0.952 | 0.635 | 0.952 | 0.968 |
