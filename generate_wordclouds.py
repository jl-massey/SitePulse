import json
import logging
import os

import matplotlib.pyplot as plt
from wordcloud import WordCloud

from scrape_websites import url_to_filename

DATA_DIR = "data"
OUTPUT_DIR = "output"
MAX_WORDS = 100
IMAGE_SIZE = (800, 600)


def generate_wordclouds(business_url: str) -> None:
    """
    Generate word clouds from TF-IDF data showing key terms for business (A) and competitors (B).
    
    Creates three word clouds:
    1. Business terms scaled by TF-IDF score
    2. Competitor terms scaled by TF-IDF score
    3. Difference (A-B) showing terms unique to or significantly more important in A
       (terms where A's score is 0 in B or at least 4x higher than B's score)

    Args:
        business_url: URL of the business website, used to find input files and name outputs
    
    Raises:
        FileNotFoundError: If TF-IDF input files are not found
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    prefix = url_to_filename(business_url)
    file_a = os.path.join(DATA_DIR, f"tfidf-{prefix}.json")
    file_b = os.path.join(DATA_DIR, f"tfidf-{prefix}-competitors.json")

    try:
        with open(file_a, "r", encoding="utf-8") as f:
            tfidf_a: dict[str, float] = json.load(f)
    except FileNotFoundError:
        logging.error("TF-IDF file not found: %s", file_a)
        raise
    try:
        with open(file_b, "r", encoding="utf-8") as f:
            tfidf_b: dict[str, float] = json.load(f)
    except FileNotFoundError:
        logging.error("TF-IDF file not found: %s", file_b)
        raise

    # Generate word clouds
    wc_a = _create_wordcloud(tfidf_a)
    wc_b = _create_wordcloud(tfidf_b)
    wc_diff = _create_wordcloud(_compute_difference(tfidf_a, tfidf_b))

    # Save images
    paths = {
        "business": os.path.join(OUTPUT_DIR, f"wc-{prefix}.png"),
        "competitors": os.path.join(OUTPUT_DIR, f"wc-{prefix}-competitors.png"),
        "difference": os.path.join(OUTPUT_DIR, f"wc-{prefix}-diff.png"),
    }
    for key, wc in [("business", wc_a), ("competitors", wc_b), ("difference", wc_diff)]:
        fig = plt.figure(figsize=(IMAGE_SIZE[0] / 100, IMAGE_SIZE[1] / 100))
        plt.imshow(wc, interpolation="bilinear")
        plt.axis("off")
        # Remove padding around the word cloud
        plt.tight_layout(pad=0)
        # Save with minimal borders
        fig.savefig(paths[key], format="png", bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        logging.info("Saved word cloud %s", paths[key])


def _create_wordcloud(tfidf_dict: dict[str, float]) -> WordCloud:
    # Internal: create a WordCloud object from term-score pairs
    wc = WordCloud(
        width=IMAGE_SIZE[0],
        height=IMAGE_SIZE[1],
        max_words=MAX_WORDS,
        background_color="gray",
    )
    wc.generate_from_frequencies(tfidf_dict)
    return wc


def _compute_difference(a: dict[str, float], b: dict[str, float], threshold: float = 0.01) -> dict[str, float]:
    # Internal: compute significant differences between TF-IDF scores
    # Only include terms that are unique to A or where A's score is at least 4x B's
    diff: dict[str, float] = {}
    for term, score_a in a.items():
        score_b = b.get(term, 0.0)
        if score_b < 0:
            score_b = 0.0
            
        # Include if term is unique to A or has significantly higher score
        if score_b == 0.0 or score_a >= 4 * score_b:
            diff_score = score_a - score_b
            if diff_score > threshold:
                diff[term] = diff_score
                
    return diff
