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
- For A - B:
    - Compute difference by comparing TF-IDF scores:
        - Include a term in the different cloud only if:
            - The term is in A but not in B (score=0 in B), or
            - The term's TF-IDF score in A is SIGNIGICANTLY higher than in B (e.g.  A's score is at least 4x B's score).
    - For each term in a, subtract B's score (if B's score is < 0, use 0).
    - If the resulting score is negative or below threshold (e.g. 0.01), exclude the term.
    - Create a workd cloud with remaining terms, scaling font size by difference score.
    - Save word cloud as PNG (`wc-www_businessA_com-diff_more.png`)
- For B - A:
    - Compute difference by comparing TF-IDF scores:
        - Include a term in the different cloud only if:
            - The term is in B but not in A (score=0 in A), or
            - The term's TF-IDF score in B is SIGNIFICANTLY higher than in A (e.g.  B's score is at least 4x A's score).
            - Save word cloud as PNG (`wc-www_businessA_com-diff_less.png`)
- Save word clouds as PNGs (`wc-www_businessA_com.png`, `wc-www_businessA_com-competitors.png`, etc) in `./output/`.
- Style: gray background, max 100 words
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
