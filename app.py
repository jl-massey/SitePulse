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
    difference: str  # Unique topics

# Prevent gio browser launch error on Linux
if platform.system() == "Linux":
    os.environ["GIO_EXTRA_MODULES"] = "/usr/lib/x86_64-linux-gnu/gio/modules/"

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
        col1, col2 = st.columns([1, 2])
        with col1:
            business_name = st.text_input(
                "Business Name",
                placeholder="Example Inc",
                help="Used to filter business-specific terms from analysis"
            )
        with col2:
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

    # Process button
    process = st.button(
        "Analyze Websites",
        help="Start content analysis",
        type="primary",
        use_container_width=True
    )

    if process:
        # Input validation
        if not business_url:
            st.error("Please enter your business website URL.")
            return

        if not is_valid_url(business_url):
            st.error("Please enter a valid business website URL.")
            return

        # Process competitor URLs
        competitor_urls = [
            url.strip() for url in competitor_input.splitlines() 
            if url.strip() and is_valid_url(url.strip())
        ]

        if not competitor_urls:
            st.error("Please enter at least one valid competitor URL.")
            return

        if len(competitor_urls) > MAX_COMPETITORS:
            st.error(f"Please enter no more than {MAX_COMPETITORS} competitor URLs.")
            return

        # Show warning if business name not provided
        if not business_name:
            st.warning(
                "Business name not provided. This may affect analysis accuracy "
                "as business-specific terms might not be filtered correctly."
            )

        try:
            # Content collection
            with st.spinner("📥 Collecting website content..."):
                scrape_websites(business_url, competitor_urls)

            # Analysis
            with st.spinner("🔍 Analyzing content differences..."):
                compute_tfidf(business_url, competitor_urls, business_name)

            # Visualization
            with st.spinner("🎨 Creating visualizations..."):
                generate_wordclouds(business_url)

            # Display results
            prefix = url_to_filename(business_url)
            paths: WordCloudPaths = {
                "business": os.path.join(OUTPUT_DIR, f"wc-{prefix}.png"),
                "competitors": os.path.join(OUTPUT_DIR, f"wc-{prefix}-competitors.png"),
                "difference": os.path.join(OUTPUT_DIR, f"wc-{prefix}-diff.png")
            }

            # Create three columns for word clouds
            col1, col2, col3 = st.columns(3, gap="medium")

            with col1:
                st.subheader("Your Topics")
                if os.path.exists(paths["business"]):
                    st.image(paths["business"], use_container_width=True)
                else:
                    st.error("Business word cloud not generated")

            with col2:
                st.subheader("Competitor Topics")
                if os.path.exists(paths["competitors"]):
                    st.image(paths["competitors"], use_container_width=True)
                else:
                    st.error("Competitor word cloud not generated")

            with col3:
                st.subheader("Unique Topics")
                if os.path.exists(paths["difference"]):
                    st.image(paths["difference"], use_container_width=True)
                else:
                    st.error("Difference word cloud not generated")

        except Exception as e:
            st.error(
                "An error occurred during processing. Please check your inputs and try again.\n\n"
                f"Error details: {str(e)}"
            )

if __name__ == "__main__":
    main()
