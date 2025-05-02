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
DIFF_THRESHOLD = 0.01  # Minimum score difference to include in diff clouds
SIGNIFICANCE_FACTOR = 4  # How many times larger a score must be to be significant

def generate_wordclouds(business_url: str) -> None:
    """
    Generate word clouds from TF-IDF data for business (A) and competitors (B).
    
    Creates four word clouds:
    1. Business terms (A) scaled by TF-IDF score.
    2. Competitor terms (B) scaled by TF-IDF score.
    3. Difference (A-B): Terms unique to A or significantly stronger in A.
    4. Difference (B-A): Terms unique to B or significantly stronger in B.

    Args:
        business_url: URL of the business website, used for file naming.
    
    Raises:
        FileNotFoundError: If required TF-IDF input files are not found.
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
    wc_diff_ab = _create_wordcloud(_compute_difference(tfidf_a, tfidf_b))
    wc_diff_ba = _create_wordcloud(_compute_difference(tfidf_b, tfidf_a))

    # Save images
    paths = {
        "business": os.path.join(OUTPUT_DIR, f"wc-{prefix}.png"),
        "competitors": os.path.join(OUTPUT_DIR, f"wc-{prefix}-competitors.png"),
        "difference_ab": os.path.join(OUTPUT_DIR, f"wc-{prefix}-diff_more.png"),
        "difference_ba": os.path.join(OUTPUT_DIR, f"wc-{prefix}-diff_less.png"),
    }
    
    # Map internal keys to the word cloud objects
    wordclouds_to_save = {
        "business": wc_a,
        "competitors": wc_b,
        "difference_ab": wc_diff_ab,
        "difference_ba": wc_diff_ba,
    }

    for key, wc in wordclouds_to_save.items():
        if not wc: # Skip if word cloud generation failed (e.g., empty diff)
            logging.warning("Skipping saving word cloud for %s as it is empty.", key)
            continue
            
        fig = plt.figure(figsize=(IMAGE_SIZE[0] / 100, IMAGE_SIZE[1] / 100))
        plt.imshow(wc, interpolation="bilinear")
        plt.axis("off")
        plt.tight_layout(pad=0)
        fig.savefig(paths[key], format="png", bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        logging.info("Saved word cloud %s", paths[key])


def _create_wordcloud(tfidf_dict: dict[str, float]) -> WordCloud | None:
    """Internal: create a WordCloud object from term-score pairs."""
    if not tfidf_dict: # Handle empty input dictionary
        return None
        
    wc = WordCloud(
        width=IMAGE_SIZE[0],
        height=IMAGE_SIZE[1],
        max_words=MAX_WORDS,
        background_color="gray",
        # Ensure scores are positive for frequency generation
        min_font_size=10 # Avoid tiny fonts
    )
    # Ensure all frequencies are positive
    positive_freq = {term: max(score, 0.001) for term, score in tfidf_dict.items()}
    try:
        wc.generate_from_frequencies(positive_freq)
        return wc
    except ValueError as e:
        # Can happen if all frequencies are effectively zero after scaling
        logging.warning("Could not generate word cloud: %s", e)
        return None


def _compute_difference(primary: dict[str, float], secondary: dict[str, float]) -> dict[str, float]:
    """
    Internal: compute significant differences (primary - secondary).
    
    Includes terms unique to primary or where primary's score is significantly 
    higher (>= SIGNIFICANCE_FACTOR * secondary's score).
    """
    diff: dict[str, float] = {}
    for term, score_primary in primary.items():
        score_secondary = secondary.get(term, 0.0)
        # Treat negative scores as zero for comparison
        score_secondary_safe = max(score_secondary, 0.0)
            
        # Include if term is unique to primary or has significantly higher score
        is_significant = False
        if score_secondary_safe == 0.0:
            is_significant = True
        elif score_primary >= SIGNIFICANCE_FACTOR * score_secondary_safe:
            is_significant = True
            
        if is_significant:
            # Calculate difference score, ensuring it's positive
            diff_score = max(score_primary - score_secondary_safe, 0.0)
            if diff_score >= DIFF_THRESHOLD:
                diff[term] = diff_score
                
    return diff
