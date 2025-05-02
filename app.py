import os
import platform

import streamlit as st

from generate_wordclouds import generate_wordclouds
from scrape_websites import scrape_websites, url_to_filename
from tfidf_analysis import compute_tfidf

OUTPUT_DIR = "output"

# Prevent gio browser launch error on Linux
if platform.system() == "Linux":
    os.environ["GIO_EXTRA_MODULES"] = "/usr/lib/x86_64-linux-gnu/gio/modules/"

def main() -> None:
    """
    Streamlit UI for SitePulse: input URLs, process pipeline, and display word clouds.
    """
    # Disable automatic browser opening
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    os.environ["STREAMLIT_SERVER_AUTO_OPEN_BROWSER"] = "false"

    st.set_page_config(page_title="SitePulse - Website Content Analysis", layout="centered")
    st.title("SitePulse")
    st.markdown(
        "Visualize and compare the key topics from your website and your competitors. "
        "See what makes your content unique and discover opportunities for improvement."
    )

    business_url = st.text_input("Your Website URL", placeholder="https://www.example.com")
    competitor_input = st.text_area(
        "Competitor Website URLs (one per line)",
        placeholder="https://www.comp1.com\nhttps://www.comp2.com",
        help="Add up to 5 competitor websites to compare against"
    )

    if st.button("Analyze Websites"):
        if not business_url:
            st.error("Please enter a business URL.")
            return
        competitor_urls = [
            url.strip() for url in competitor_input.splitlines() if url.strip()
        ]

        try:
            with st.spinner("Collecting website content..."):
                scrape_websites(business_url, competitor_urls)  # type: ignore
            with st.spinner("Analyzing content..."):
                compute_tfidf(business_url, competitor_urls)  # type: ignore
            with st.spinner("Creating visualizations..."):
                generate_wordclouds(business_url)  # type: ignore

            prefix = url_to_filename(business_url)
            paths = {
                "Your Website Topics": os.path.join(OUTPUT_DIR, f"wc-{prefix}.png"),
                "Competitor Topics": os.path.join(OUTPUT_DIR, f"wc-{prefix}-competitors.png"),
                "Your Unique Topics": os.path.join(OUTPUT_DIR, f"wc-{prefix}-diff.png"),
            }

            for title, img_path in paths.items():
                st.subheader(title)
                if os.path.exists(img_path):
                    st.image(img_path, use_container_width=True)
                else:
                    st.error(f"Image not found: {img_path}")
        except Exception as e:
            st.error(f"Processing error: {e}")


if __name__ == "__main__":
    main()
