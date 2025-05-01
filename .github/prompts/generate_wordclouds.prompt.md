---
mode: 'agent'
---
# Generate Word Clouds Prompt
## Purpose
Create word clouds for business (A), competitors (B), and difference (A - B) using TF-IDF data.

## Instructions
- Use `wordcloud` and `matplotlib` to generate word clouds.
- Input: `tfidf-www_businessA_com.json` and `tfidf-www_businessA_com-competitors.json` from `./data/`.
- For A, B: Generate word clouds from term-score pairs, scaling font size by score.
- For A - B: Compute difference (terms in A with higher scores or absent in B), create word cloud.
- Save word clouds as PNGs (`wc-www_businessA_com.png`, `wc-www_businessA_com-competitors.png`, `wc-www_businessA_com-diff.png`) in `./output/`.
- Style: gray background, max 100 words, font size proportional to score.
- Handle file input errors.
- Follow Python PEP 8, use snake_case.
- Add docstrings for public functions; skip private (e.g., `_scale_scores`).
- Run with `uv run python script.py`.
- Use Python 3.12+ type hints.

## Context
- Project uses Python 3.12+, `uv` for dependencies.
- Dependencies: `wordcloud`, `matplotlib` (via `uv add`).
- Image dimensions: 800x600 pixels.

## Notes to agent
- `www_businessA_com` is a placeholder for the actual business URL. Use the input URL in the code.
