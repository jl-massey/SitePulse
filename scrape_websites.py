import asyncio
import logging
import os
import re
from collections import defaultdict
from typing import DefaultDict
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

# Configure logging format to include level
logging.basicConfig(
    format='%(levelname)s:%(message)s',
    level=logging.INFO
)

DATA_DIR = "data"
MAX_REDIRECTS = 2
MAX_RETRIES = 1
PAGE_TIMEOUT = 5

# Priority paths to check first
PRIORITY_PATHS = [""]

# Track warning counts to avoid spam
warning_counts: DefaultDict[str, int] = defaultdict(int)
MAX_SIMILAR_WARNINGS = 3

def log_warning(message: str, *args) -> None:
    """Rate-limit similar warnings to reduce noise."""
    key = message % args if args else message
    if warning_counts[key] < MAX_SIMILAR_WARNINGS:
        warning_counts[key] += 1
        if warning_counts[key] == MAX_SIMILAR_WARNINGS:
            logging.warning("%s (suppressing further similar warnings)", key)
        else:
            logging.warning(key)


def url_to_filename(url: str) -> str:
    """
    Convert a URL into a safe filename prefix.
    """
    parsed = urlparse(url)
    netloc = parsed.netloc or parsed.path
    netloc_clean = re.sub(r"[^0-9a-zA-Z]+", "_", netloc)
    return re.sub(r"_+", "_", netloc_clean)


def scrape_websites(business_url: str, competitor_urls: list[str]) -> None:
    """
    Scrape text from a business website and competitor websites.
    Focuses on homepage and 'about' pages, saves cleaned text to files.

    Args:
        business_url: URL of the business website
        competitor_urls: List of competitor website URLs
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    urls = [business_url] + competitor_urls
    for url in urls:
        prefix = url_to_filename(url)
        filename = f"site-{prefix}.txt"
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            logging.info("Skipping existing file: %s", filepath)
            continue
        try:
            text = asyncio.run(_crawl_and_clean_site(url))
            if not text.strip():
                logging.warning("No content extracted from %s", url)
                continue
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            logging.info("Saved scraped text to %s", filepath)
        except Exception as e:
            logging.error("Error scraping %s: %s", url, e)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("")  # Create empty file to skip on next run
            continue  # Skip instead of raise to process all sites


async def _crawl_and_clean_site(url: str, max_depth: int = 1) -> str:
    """
    Internal: Aggressively crawl homepage and about pages for text content.
    """
    base_netloc = urlparse(url).netloc
    visited: set[str] = set()
    texts: list[str] = []
    
    # Start with priority paths
    base_url = f"{urlparse(url).scheme}://{base_netloc}"
    priority_urls = [
        urljoin(base_url, path)
        for path in PRIORITY_PATHS
    ]

    # Headers to prevent downloading media/images
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain",
        "Accept-Encoding": "gzip, deflate",
        "User-Agent": "Mozilla/5.0 SitePulse/1.0"
    }
    
    limits = httpx.Limits(max_keepalive_connections=3, max_connections=3)
    transport = httpx.AsyncHTTPTransport(retries=MAX_RETRIES)
    
    # Create client with relaxed SSL verification for problematic sites
    verify = httpx.create_ssl_context(verify=True)
    verify.check_hostname = False  # Allow hostname mismatch
    
    async with httpx.AsyncClient(
        timeout=PAGE_TIMEOUT,
        limits=limits,
        transport=transport,
        follow_redirects=True,
        max_redirects=MAX_REDIRECTS,
        headers=headers,
        verify=verify
    ) as client:
        # First check priority URLs
        for page_url in priority_urls:
            if page_url in visited:
                continue
            visited.add(page_url)
            
            try:
                resp = await client.get(page_url)
                if resp.status_code == 404:
                    # Log 404s at debug level to reduce noise
                    logging.debug("Page not found: %s", page_url)
                    continue
                resp.raise_for_status()
                
                if not resp.text or not resp.text.strip():
                    logging.debug("Empty response from %s", page_url)
                    continue
                    
                html = resp.text
                raw_text = _extract_text(html)
                if raw_text.strip():
                    texts.append(raw_text)
                    
                # Look for more about/company pages
                if len(texts) < 3:  # Limit additional crawling
                    soup = BeautifulSoup(html, "html.parser")
                    for a in soup.find_all('a', href=True):
                        href = a['href'].lower()
                        if any(term in href for term in ['about', 'company', 'who']):
                            link = urljoin(page_url, href)
                            if (urlparse(link).netloc == base_netloc 
                                and link not in visited):
                                visited.add(link)
                                try:
                                    resp = await client.get(link)
                                    if resp.status_code == 404:
                                        continue
                                    resp.raise_for_status()
                                    if resp.text.strip():
                                        raw_text = _extract_text(resp.text)
                                        if raw_text.strip():
                                            texts.append(raw_text)
                                except httpx.HTTPError:
                                    continue  # Silently skip errors on secondary pages
            except httpx.HTTPStatusError as e:
                log_warning("Error fetching %s: %s", page_url, str(e))
            except httpx.SSLError as e:
                log_warning("SSL error for %s: %s", page_url, str(e))
            except Exception as e:
                log_warning("Error fetching %s: %s", page_url, str(e))
                    
    return "\n".join(texts)


def _extract_text(html: str) -> str:
    # Parse HTML and extract visible text
    soup = BeautifulSoup(html, "html.parser")
    for script in soup(["script", "style", "nav"]):
        script.decompose()
    tags = soup.find_all(["p", "h1", "h2", "h3", "div"])
    texts = [tag.get_text(separator=" ", strip=True) for tag in tags]
    return "\n".join(text for text in texts if text)


def _clean_text(text: str) -> str:
    # Remove non-alphanumeric characters and collapse whitespace
    text = re.sub(r"[^0-9a-zA-Z\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
