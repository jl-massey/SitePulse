import argparse
import json
import logging
import os
import re
from urllib.parse import urlparse

import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer

from scrape_websites import url_to_filename

# Download NLTK data
nltk.download('stopwords', quiet=True)

DATA_DIR = "data"
TOP_N = 100


def _get_business_name(url: str) -> str:
    """Extract business name from URL to filter from analysis."""
    domain = urlparse(url).netloc.lower()
    # Remove common prefixes and suffixes
    name = re.sub(r'^www\.', '', domain)
    name = re.sub(r'\.com.*$|\.org.*$|\.net.*$', '', name)
    return name


def compute_tfidf(business_url: str, competitor_urls: list[str]) -> None:
    """
    Compute TF-IDF scores for business (A) and competitor (B) websites.
    
    Processes text files from data directory, removes business name references,
    and generates TF-IDF scores using scikit-learn. Treats all competitors as
    a single group. Outputs top 100 terms by score for each group as JSON.
    
    Args:
        business_url: URL of the business website
        competitor_urls: List of competitor website URLs
    
    Raises:
        FileNotFoundError: If input text files are not found
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    # Extract business name to filter out
    business_name = _get_business_name(business_url)
    name_pattern = re.compile(fr'\b{business_name}\b', re.IGNORECASE)

    # Load and preprocess business text
    business_prefix = url_to_filename(business_url)
    business_path = os.path.join(DATA_DIR, f"site-{business_prefix}.txt")
    try:
        with open(business_path, "r", encoding="utf-8") as f:
            business_text = f.read().strip()
            if not business_text:
                raise ValueError(f"Business file is empty: {business_path}")
            # Remove business name references and check if content remains
            business_text = name_pattern.sub('', business_text).strip()
            if not business_text:
                raise ValueError(f"No content remains after filtering business name from {business_path}")
    except FileNotFoundError:
        logging.error("Business data file not found: %s", business_path)
        raise

    # Load competitor texts
    competitor_texts = []
    skipped_competitors = []
    for url in competitor_urls:
        prefix = url_to_filename(url)
        path = os.path.join(DATA_DIR, f"site-{prefix}.txt")
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read().strip()
                if not text:  # Skip empty files
                    skipped_competitors.append(url)
                    continue
                # Remove business name from competitor texts
                text = name_pattern.sub('', text)
                if text.strip():  # Only add if there's content after filtering
                    competitor_texts.append(text)
        except FileNotFoundError:
            logging.warning("Competitor data file not found: %s", path)
            skipped_competitors.append(url)
            continue

    if not competitor_texts:
        raise ValueError("No valid competitor texts found - all files were empty or missing")

    if skipped_competitors:
        logging.warning("Skipped %d competitors due to empty/missing files: %s", 
                       len(skipped_competitors), ", ".join(skipped_competitors))

    # Combine competitors into single document
    competitors_doc = "\n".join(competitor_texts)

    # Configure vectorizer with robust settings
    vectorizer = TfidfVectorizer(
        stop_words="english",
        lowercase=True,
        max_features=1000,
        token_pattern=r'(?u)\b[A-Za-z][A-Za-z]+\b',
        ngram_range=(1, 2),
        min_df=1,  # Include terms that appear in at least one document
        max_df=1.0,  # Include all terms regardless of document frequency
    )

    # Generate TF-IDF matrices with error checking
    docs = [business_text, competitors_doc]
    try:
        tfidf_matrix = vectorizer.fit_transform(docs)
    except ValueError as e:
        logging.error("TF-IDF computation failed: %s", str(e))
        raise ValueError("TF-IDF computation failed - check if documents contain valid text content") from e
    
    if tfidf_matrix.nnz == 0:  # Check if matrix is all zeros
        raise ValueError("TF-IDF computation produced no results - documents may not contain enough valid text")
    feature_names = vectorizer.get_feature_names_out()

    # Extract scores from sparse matrix
    scores_a = tfidf_matrix[0].toarray()[0]
    scores_b = tfidf_matrix[1].toarray()[0]

    # Create term-score mappings
    tfidf_a: dict[str, float] = {}
    tfidf_b: dict[str, float] = {}
    for term, sa, sb in zip(feature_names, scores_a, scores_b):
        tfidf_a[term] = float(sa)
        tfidf_b[term] = float(sb)

    # Get top N terms by score
    top_a = dict(sorted(tfidf_a.items(), key=lambda x: x[1], reverse=True)[:TOP_N])
    top_b = dict(sorted(tfidf_b.items(), key=lambda x: x[1], reverse=True)[:TOP_N])

    # Save JSON outputs
    out_a = os.path.join(DATA_DIR, f"tfidf-{business_prefix}.json")
    out_b = os.path.join(DATA_DIR, f"tfidf-{business_prefix}-competitors.json")
    with open(out_a, "w", encoding="utf-8") as f:
        json.dump(top_a, f, indent=2)
    with open(out_b, "w", encoding="utf-8") as f:
        json.dump(top_b, f, indent=2)
    logging.info("TF-IDF results saved: %s, %s", out_a, out_b)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute TF-IDF scores for business and competitors.")
    parser.add_argument("--business-url", required=True, help="Business website URL")
    parser.add_argument("--competitors", nargs="+", required=True, help="Competitor website URLs")
    args = parser.parse_args()
    compute_tfidf(args.business_url, args.competitors)
