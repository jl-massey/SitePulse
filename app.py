import os
import platform
from typing import TypedDict
from urllib.parse import urlparse

import streamlit as st

from generate_wordclouds import generate_wordclouds
from scrape_websites import scrape_websites, url_to_filename
from tfidf_analysis import compute_tfidf

# Configuration
OUTPUT_DIR = "output"
MAX_COMPETITORS = 5

class WordCloudPaths(TypedDict):
    """Type definition for word cloud image paths."""
    business: str  # Your website topics
    competitors: str  # Competitor topics
    diff_more: str  # Topics you have more (A-B)
    diff_less: str  # Topics competitors favor (B-A)

# Prevent gio browser launch error on Linux
if platform.system() == "Linux":
    os.environ["GIO_EXTRA_MODULES"] = "/usr/lib/x86_64-linux-gnu/gio/modules/"


def normalize_url(url: str) -> str:
    """
    Normalize a URL by ensuring it has a proper scheme (http:// or https://).
    
    Args:
        url: The URL to normalize, with or without a scheme.
        
    Returns:
        str: A URL with a proper scheme (uses https:// by default).
    """
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme in ['http', 'https']:
        return url
    if url.startswith('//'):
        return f"https:{url}"
    return f"https://{url}"


def is_valid_url(url: str) -> bool:
    """Validate URL format."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def main() -> None:
    """
    Streamlit UI for SitePulse: A website content analysis tool.
    
    Features:
    - Input business name and URLs
    - Process web content
    - Display comparative word clouds
    """
    # Disable automatic browser opening
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    os.environ["STREAMLIT_SERVER_AUTO_OPEN_BROWSER"] = "false"

    # Page configuration
    st.set_page_config(
        page_title="SitePulse - Website Content Analysis",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Header
    st.title("SitePulse")
    st.markdown(
        "Visualize and compare key topics from your website against competitors. "
        "Discover what makes your content unique and identify opportunities for improvement."
    )

    # Business section
    with st.container():
        st.subheader("Your Business")
        business_url = st.text_input(
            "Website URL",
            placeholder="https://www.example.com",
            help="Your company's website address"
        )

    # Competitor section
    st.subheader("Competitors")
    competitor_input = st.text_area(
        "Website URLs",
        placeholder=(
            "Enter up to 5 competitor websites (one per line):\n"
            "https://www.competitor1.com\n"
            "https://www.competitor2.com"
        ),
        help=f"Maximum {MAX_COMPETITORS} competitors"
    )

    # Filter section
    st.subheader("Filter")
    filter_words_input = st.text_input(
        "Words to remove from the cloud (comma delimited)",
        placeholder="e.g., company, business, solution",
        help="Enter words to exclude from the analysis, separated by commas."
    )

    # Process button
    process = st.button(
        "Analyze Websites",
        help="Start content analysis",
        type="primary",
        use_container_width=True
    )

    if process:
        if not business_url:
            st.error("Please enter your business website URL.")
            return

        business_url = normalize_url(business_url)

        if not is_valid_url(business_url):
            st.error("Please enter a valid business website URL.")
            return

        competitor_urls = [
            normalize_url(url.strip()) for url in competitor_input.splitlines() 
            if url.strip() and is_valid_url(normalize_url(url.strip()))
        ]

        if not competitor_urls:
            st.error("Please enter at least one valid competitor URL.")
            return

        if len(competitor_urls) > MAX_COMPETITORS:
            st.error(f"Please enter no more than {MAX_COMPETITORS} competitor URLs.")
            return
        
        # Process filter words
        filter_words = [word.strip().lower() for word in filter_words_input.split(',') if word.strip()]

        try:
            # Content collection
            with st.spinner("📥 Collecting website content..."):
                scrape_websites(business_url, competitor_urls)

            # Analysis
            with st.spinner("🔍 Analyzing content differences..."):
                compute_tfidf(business_url, competitor_urls, filter_words) 

            # Visualization
            with st.spinner("🎨 Creating visualizations..."):
                generate_wordclouds(business_url)

            # Display results
            prefix = url_to_filename(business_url)
            paths: WordCloudPaths = {
                "business": os.path.join(OUTPUT_DIR, f"wc-{prefix}.png"),
                "competitors": os.path.join(OUTPUT_DIR, f"wc-{prefix}-competitors.png"),
                "diff_more": os.path.join(OUTPUT_DIR, f"wc-{prefix}-diff_more.png"), # A-B
                "diff_less": os.path.join(OUTPUT_DIR, f"wc-{prefix}-diff_less.png"), # B-A
            }

            # --- Topic Comparison Section ---
            st.write("### Topic Comparison")
            comparison_cols = st.columns([1, 1])
            
            with comparison_cols[0]:
                st.write("#### You (A)")
                if os.path.exists(paths["business"]):
                    st.image(
                        paths["business"],
                        use_container_width="always",
                        output_format="PNG"
                    )
                else:
                    st.error("Business word cloud not generated")

            with comparison_cols[1]:
                st.write("#### Competitors (B)")
                if os.path.exists(paths["competitors"]):
                    st.image(
                        paths["competitors"],
                        use_container_width="always",
                        output_format="PNG"
                    )
                else:
                    st.error("Competitor word cloud not generated")

            # --- Difference Section ---
            st.write("### Difference Analysis")
            diff_cols = st.columns([1, 1])

            with diff_cols[0]:
                st.write("#### You Have More (A-B)")
                if os.path.exists(paths["diff_more"]):
                    st.image(
                        paths["diff_more"],
                        use_container_width="always",
                        output_format="PNG"
                    )
                else:
                    st.error("A-B difference word cloud not generated")

            with diff_cols[1]:
                st.write("#### Competitors Favor (B-A)")
                if os.path.exists(paths["diff_less"]):
                    st.image(
                        paths["diff_less"],
                        use_container_width="always",
                        output_format="PNG"
                    )
                else:
                    st.error("B-A difference word cloud not generated")

        except Exception as e:
            st.error(
                "An error occurred during processing. Please check your inputs and try again.\n\n"
                f"Error details: {str(e)}"
            )

if __name__ == "__main__":
    main()
