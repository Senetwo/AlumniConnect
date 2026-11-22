# Ask-the-library retrieval evaluation (24 answerable and 6 out-of-library questions, 12 documents)

Similarity floor for the embedding systems: 0.25. The substring and TF-IDF scores are not on the same scale, so the last two columns apply only to the embedding systems.

| System | Hit@1 | Hit@3 | MRR | Answerable questions above floor | Out-of-library declined |
|---|---|---|---|---|---|
| substring | 0.000 | 0.000 | 0.083 | n/a | n/a |
| tfidf-keyword | 0.500 | 0.792 | 0.664 | n/a | n/a |
| base-minilm | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| fine-tuned | 0.958 | 1.000 | 0.979 | 1.000 | 1.000 |

Lowest similarity of a correct document and highest similarity of an out-of-library question (embedding systems):

- base-minilm: lowest correct 0.408, highest out-of-library 0.221
- fine-tuned: lowest correct 0.449, highest out-of-library 0.173
