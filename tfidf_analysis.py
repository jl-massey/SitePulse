import argparse
import json
import logging
from pathlib import Path

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

from scrape_websites import url_to_filename

# Download required NLTK data
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)

DATA_DIR = "data"
TOP_N = 100

def _get_business_terms(name: str | None = None, url: str | None = None) -> set[str]:
    """Build set of business terms to filter from texts."""
    terms = set()
    
    # Add terms from provided name if available
    if name:
        # Tokenize and clean name
        tokens = word_tokenize(name.lower())
        # Add individual words and pairs
        for token in tokens:
            if token.isalpha() and token not in stopwords.words('english'):
                terms.add(token)
        # Add word pairs without punctuation or stopwords
        clean_tokens = [t for t in tokens if t.isalpha() and t not in stopwords.words('english')]
        for i in range(len(clean_tokens)-1):
            terms.add(f"{clean_tokens[i]} {clean_tokens[i+1]}")
            terms.add(f"{clean_tokens[i]}{clean_tokens[i+1]}")
    
    # Extract terms from URL as backup
    if url:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        # Strip www. and TLD
        name = domain.replace('www.', '').split('.')[0]
        # Split on non-letters and add parts
        parts = ''.join(c if c.isalpha() else ' ' for c in name).split()
        terms.update(p for p in parts if p not in stopwords.words('english'))
        # Add the full domain name too
        domain_name = ''.join(c for c in name if c.isalpha())
        if domain_name:
            terms.add(domain_name)
            
    return terms

def compute_tfidf(business_url: str, competitor_urls: list[str], business_name: str | None = None) -> None:
    """
    Compute TF-IDF scores for business and competitor websites.
    
    Processes website content, removes business name references, and generates 
    TF-IDF scores. Treats all competitors as a single group. Outputs top terms 
    by score as JSON. If business_name is not provided, extracts it from URL.
    
    Args:
        business_url: URL of the business website
        competitor_urls: List of competitor website URLs
        business_name: Optional business name to filter from analysis
    """
    data_dir = Path(DATA_DIR)
    data_dir.mkdir(exist_ok=True)
    
    # Get business terms to filter out
    business_terms = _get_business_terms(business_name, business_url)
    if not business_terms:
        logging.warning("No business terms identified for filtering")
    else:
        logging.info("Business terms to filter: %s", sorted(business_terms))
        
    # Load and preprocess business text
    business_prefix = url_to_filename(business_url)
    business_path = data_dir / f"site-{business_prefix}.txt"
    
    try:
        with open(business_path, encoding='utf-8') as f:
            text = f.read().lower()  # Lowercase early
            
        if not text.strip():
            business_path.unlink()  # Delete empty file
            raise ValueError(f"Business file is empty: {business_path}")
            
        # Remove punctuation and numbers
        text = ''.join(c for c in text if c.isalpha() or c.isspace())
        # Tokenize
        tokens = word_tokenize(text)
        # Remove stopwords and business terms
        stop_words = set(stopwords.words('english'))
        tokens = [t for t in tokens if t not in stop_words and t not in business_terms]
        
        if not tokens:
            business_path.unlink()  # Delete if no valid content remains
            raise ValueError(f"No valid content after filtering: {business_path}")
            
        business_text = ' '.join(tokens)
            
    except FileNotFoundError:
        raise FileNotFoundError(f"Business file not found: {business_path}")
        
    # Process competitor texts
    competitor_texts = []
    skipped = []
    
    for url in competitor_urls:
        prefix = url_to_filename(url)
        path = data_dir / f"site-{prefix}.txt"
        
        try:
            with open(path, encoding='utf-8') as f:
                text = f.read().lower()
                
            if not text.strip():
                path.unlink()  # Delete empty file
                skipped.append(url)
                continue
                
            # Same preprocessing as business text
            text = ''.join(c for c in text if c.isalpha() or c.isspace())
            tokens = word_tokenize(text)
            tokens = [t for t in tokens if t not in stop_words and t not in business_terms]
            
            if tokens:
                competitor_texts.append(' '.join(tokens))
            else:
                path.unlink()  # Delete if no valid content
                skipped.append(url)
                
        except FileNotFoundError:
            skipped.append(url)
            continue
            
    if skipped:
        logging.warning("Skipped %d competitors: %s", len(skipped), skipped)
    
    if not competitor_texts:
        raise ValueError("No valid competitor texts found after preprocessing")
        
    # Combine all competitor texts
    competitor_doc = '\n'.join(competitor_texts)
    
    # Configure vectorizer (many preprocessing steps already done)
    vectorizer = TfidfVectorizer(
        lowercase=False,  # Already done
        stop_words=None,  # Already removed
        token_pattern=r'(?u)\b\w+\b',  # Simple word pattern
        max_features=1000,
        ngram_range=(1, 2)  # Include bigrams
    )
    
    # Generate TF-IDF matrices
    try:
        tfidf_matrix = vectorizer.fit_transform([business_text, competitor_doc])
        if tfidf_matrix.nnz == 0:
            raise ValueError("TF-IDF computation produced empty result")
            
        # Get terms and scores
        terms = vectorizer.get_feature_names_out()
        business_scores = tfidf_matrix[0].toarray()[0]
        competitor_scores = tfidf_matrix[1].toarray()[0]
        
        # Create outputs (convert numpy types to native)
        business_terms = {
            str(term): float(score)
            for term, score in zip(terms, business_scores)
            if score > 0
        }
        competitor_terms = {
            str(term): float(score)
            for term, score in zip(terms, competitor_scores)
            if score > 0
        }
        
        # Get top terms
        top_business = dict(
            sorted(business_terms.items(), key=lambda x: x[1], reverse=True)[:TOP_N]
        )
        top_competitors = dict(
            sorted(competitor_terms.items(), key=lambda x: x[1], reverse=True)[:TOP_N]
        )
        
        # Save results
        out_business = data_dir / f"tfidf-{business_prefix}.json"
        out_competitors = data_dir / f"tfidf-{business_prefix}-competitors.json"
        
        with open(out_business, 'w', encoding='utf-8') as f:
            json.dump(top_business, f, indent=2)
            
        with open(out_competitors, 'w', encoding='utf-8') as f:
            json.dump(top_competitors, f, indent=2)
            
        logging.info("TF-IDF analysis complete, files saved: %s, %s", 
                    out_business, out_competitors)
                    
    except Exception as e:
        logging.error("TF-IDF computation failed: %s", e)
        raise ValueError("TF-IDF computation failed - check input data") from e

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute TF-IDF scores for business and competitor websites"
    )
    parser.add_argument("--business-url", required=True, help="Business website URL")
    parser.add_argument(
        "--competitors", 
        nargs="+", 
        required=True,
        help="Competitor website URLs"
    )
    parser.add_argument(
        "--business-name",
        required=False,
        help="Optional business name to filter from analysis"
    )
    args = parser.parse_args()
    compute_tfidf(args.business_url, args.competitors, args.business_name)
