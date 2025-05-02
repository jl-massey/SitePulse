---
mode: 'agent'
---
# Streamlit UI Prompt
## Purpose
Build a Streamlit app to input URLs and display word clouds for SitePulse.

## Instructions
- Use `streamlit` to create a web UI.
- Features:
  - Input fields for business URL (A), multiple competitor URLs (B) and Filtered words (comma delimited).
  - One button to trigger scraping, TF-IDF, and word cloud generation.
  - Display four word clouds (`wc-www_businessA_com.png`, `wc-www_businessA_com-competitors.png`, `wc-www_businessA_com-diff_more.png`, `wc-www_businessA_com-diff_more.png`, `wc-www_businessA_com-diff_less.png`) from `./output/`.
- Layout: Clean, centered, with headings for “Business”, “Competitors”, “Difference”.
- Ensure that the app is responsive and works on different screen sizes and devices.
- Include a progress spinner during processing.
- Handle errors (invalid URLs, missing files) with user-friendly messages.
- Save as `app.py` in project root.
- Follow Python PEP 8, use snake_case.
- Add docstrings for public functions; skip private.
- Use Python 3.12+ type hints.

## Context
- Project uses Python 3.12+, `uv` for dependencies.
- Dependency: `streamlit` (via `uv add`).
- Reference `#file:scrape_websites.prompt.md`, `#file:tfidf_analysis.prompt.md`, `#file:generate_wordclouds.prompt.md` for pipeline.
- Run with `uv run streamlit run app.py`.

## Notes to agent
- `www_businessA_com` is a placeholder for the actual business URL. Use the input URL in the code.
