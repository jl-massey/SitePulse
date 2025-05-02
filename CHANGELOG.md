# Update scrape_websites.py
- Updated to use `httpx` for async website scraping
- Added recursive crawler with max depth 2 for each site
- Updated type hints to Python 3.12+ style `list[str]`
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2025-05-02

- feat: add website scraping module (`scrape_websites.py`)
- feat: implement TF-IDF analysis (`tfidf_analysis.py`)
- feat: generate word clouds (`generate_wordclouds.py`)
- feat: create Streamlit UI (`app.py`)
