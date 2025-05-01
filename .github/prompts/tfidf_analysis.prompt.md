---
mode: 'agent'
---
# TF-IDF Analysis Prompt
## Purpose
Compute TF-IDF scores for text from business (A) and competitors (B) to identify key terms.

## Instructions
- Use `scikit-learn`’s `TfidfVectorizer` for TF-IDF analysis.
- Input: `site-www_businssA_com.txt` and all competitors (`site-www_businessB1_com.txt`, `site-www_businessB2_com.txt`, etc.) from `./data/`.
- Treat all competitors as a single group (B).
- Preprocess: lowercase, remove stop words (use NLTK’s English stop words), and tokenize. If this is built in to the `TfidfVectorizer`, you can skip this step.
- Generate TF-IDF matrices for A and B separately.
- Extract top 100 terms by TF-IDF score for each.
- Output: Two JSON files (`tfidf-www_businessA_com.json`, `tfidf-www_businessA_com-competitors.json`) with term-score pairs.
- Include error handling for file reading and processing.
- Follow Python PEP 8, use snake_case.
- Add docstrings for public functions; skip private (e.g., `_preprocess_text`).
- Run with `uv run python script.py`.
- Use Python 3.12+ type hints (e.g., `dict[str, float]`).

## Context
- Project uses Python 3.12+, `uv` for dependencies.
- Dependencies: `scikit-learn`, `nltk` (via `uv add`).
- Store outputs in `./data/`.
- Ensure reproducibility with random seed `1979`.

## Notes to agent
- `www_businessA_com` is a placeholder for the actual business URL. Use the input URL in the code.
