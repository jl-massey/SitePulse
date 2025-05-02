---
mode: 'agent'
---
# Scrape Websites Prompt
## Purpose
Scrape text content from a business website (A) and a list of competitor websites (B) using Python.

## Instructions
- Use `httpx` and `beautifulsoup4` for asynchronous HTTP requests and HTML parsing.
- Input: URL for business site (A) and a list of competitor URLs (B).
- Extract text from `<p>`, `<h1>`, `<h2>`, `<h3>`, and `<div>` tags, ignoring scripts, styles, and navigation menus.
- Limit naviation depth to 2 levels.
- Prioritize speed and efficiency for scraping. Avoid any non-text elements unless it's a SPA.  Be impatient and aggressive.
- The landing page and any 'about us', 'about', 'who we are', etc. pages are priority.
- Clean text: remove extra whitespace, special characters, and non-alphanumeric content.
- Output: Site text in text files (`site-www_businessA_com.txt`, `site-www_businessB1_com.txt`, `site-www_businessB2_com.txt`) with cleaned text.
- If a file exists for a site, do not rescrape it.
- Handle errors (e.g., invalid URLs, connection issues) with logging.
- Follow Python PEP 8, use snake_case.
- Add docstrings for public functions; skip private (e.g., `_clean_text`).
- Use `uv run python script.py` for execution.
- Use Python 3.12+ type hints (e.g., `list[str]`).

## Context
- Project uses Python 3.12+.
- Dependencies: `requests`, `beautifulsoup4`.
- Save outputs in `./data/` directory.

## Notes to agent
- `www_businessA_com` is a placeholder for the actual business URL. Use the input URL in the code.
