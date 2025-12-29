import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from modules.analyzer import FlavorAnalyzer, load_processed_data, save_analysis_results
from modules.data_cleaner import clean_records, save_json as save_clean_json
from modules.scorer import (
    get_golden_candidate,
    get_rejected_flavors,
    score_flavor_recommendations,
)
from modules.scraper import scrape_reddit, save_to_json
from modules.scraper_amazon import scrape_amazon_reviews_simple
from modules.visualizer import (
    create_brand_fit_chart,
    create_flavor_frequency_chart,
    create_score_breakdown_chart,
    create_score_comparison_chart,
    create_sentiment_gauge,
    create_sentiment_pie_chart,
    create_trend_timeline,
    create_wordcloud_image,
)


DATA_DIR = Path("data")
RAW_PATH = DATA_DIR / "raw_comments.json"
PROCESSED_PATH = DATA_DIR / "processed_data.json"
ANALYSIS_PATH = DATA_DIR / "analysis_results.json"
SCORED_PATH = DATA_DIR / "scored_recommendations.json"


st.set_page_config(
    page_title="Flavor Scout – HealthKart",
    page_icon="🍯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Header
st.title("🍯 Flavor Scout")
st.markdown("### AI-Powered Flavor Discovery Dashboard for HealthKart")
st.caption("Mining Reddit conversations to recommend next-gen product flavors using AI analysis")


def get_reddit_secrets():
    """Get Reddit credentials from Streamlit secrets or environment variables."""
    # Try Streamlit secrets first
    if "reddit" in st.secrets:
        sec = st.secrets["reddit"]
        client_id = sec.get("client_id")
        client_secret = sec.get("client_secret")
        user_agent = sec.get("user_agent", "flavor-scout-app")
        if client_id and client_secret:
            return client_id, client_secret, user_agent
    
    # Fallback to environment variables (useful for Railway)
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "flavor-scout-app")
    
    if client_id and client_secret:
        return client_id, client_secret, user_agent
    
    return None, None, "flavor-scout-app"


def get_rapidapi_secrets():
    """Get RapidAPI key from Streamlit secrets or environment variables."""
    # Try Streamlit secrets first
    if "rapidapi" in st.secrets:
        api_key = st.secrets["rapidapi"].get("api_key")
        if api_key:
            return api_key
    
    # Fallback to environment variables
    api_key = os.getenv("RAPIDAPI_KEY")
    if api_key:
        return api_key
    
    return None


def get_llm_secrets():
    """Get LLM API credentials from Streamlit secrets or environment variables."""
    provider = "anthropic"  # Default to Anthropic
    api_key = None
    model = None

    # Try Streamlit secrets first
    if "anthropic" in st.secrets:
        provider = "anthropic"
        api_key = st.secrets["anthropic"].get("api_key")
        model = st.secrets["anthropic"].get("model", "claude-3-5-sonnet-20241022")
    elif "openai" in st.secrets:
        provider = "openai"
        api_key = st.secrets["openai"].get("api_key")
        model = st.secrets["openai"].get("model", "gpt-4")
    
    # Fallback to environment variables (useful for Railway)
    if not api_key:
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if anthropic_key:
            provider = "anthropic"
            api_key = anthropic_key
            model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        elif openai_key:
            provider = "openai"
            api_key = openai_key
            model = os.getenv("OPENAI_MODEL", "gpt-4")

    return provider, api_key, model


with st.sidebar:
    st.header("Controls")
    st.write("Use these options while prototyping locally.")
    
    st.subheader("Data Source")
    data_source = st.selectbox(
        "Choose data source",
        ["Amazon Reviews (RapidAPI)", "Reddit"],
        help="Amazon Reviews: Fast setup, no approval needed. Reddit: Requires commercial approval."
    )
    
    st.subheader("Data Collection")
    
    if data_source == "Amazon Reviews (RapidAPI)":
        st.info("💡 **Recommended**: No approval needed, commercial use allowed!")
        fetch_data = st.button("Fetch Amazon product reviews")
        
        # Amazon-specific settings
        product_asins_input = st.text_area(
            "Amazon Product ASINs (one per line)",
            placeholder="B08XYZ123\nB09ABC456\nB10DEF789",
            help="Find ASINs in Amazon product URLs: amazon.in/dp/ASIN_HERE"
        )
        max_reviews = st.slider("Max reviews per product", min_value=10, max_value=200, value=50, step=10)
        limit = max_reviews  # For compatibility
        days = 90  # Not used for Amazon but kept for compatibility
        
    else:  # Reddit
        st.warning("⚠️ **Reddit requires commercial approval**. See REDDIT_COMPLIANCE.md")
        fetch_data = st.button("Fetch latest Reddit data")
        limit = st.slider("Items per query", min_value=50, max_value=300, value=100, step=50)
        days = st.slider("Lookback window (days)", min_value=7, max_value=180, value=90, step=7)
    
    st.divider()
    
    st.subheader("AI Analysis")
    run_analysis = st.button("Run AI Analysis", type="primary")
    batch_size = st.slider("Batch size for AI", min_value=5, max_value=30, value=15, step=5)


if fetch_data:
    if data_source == "Amazon Reviews (RapidAPI)":
        # Amazon Reviews scraping
        api_key = get_rapidapi_secrets()
        if not api_key:
            st.error(
                "RapidAPI key missing. Add to `.streamlit/secrets.toml`:\n"
                "```toml\n[rapidapi]\napi_key = 'your_rapidapi_key'\n```\n\n"
                "Get your key from: https://rapidapi.com"
            )
        elif not product_asins_input.strip():
            st.error("Please enter at least one Amazon product ASIN.")
        else:
            # Parse ASINs from input
            product_asins = [asin.strip() for asin in product_asins_input.strip().split("\n") if asin.strip()]
            
            with st.spinner(f"Fetching reviews from {len(product_asins)} product(s)… this may take a minute."):
                try:
                    raw = scrape_amazon_reviews_simple(
                        product_ids=product_asins,
                        api_key=api_key,
                        max_reviews=max_reviews,
                    )
                    save_to_json(raw, RAW_PATH)
                    cleaned = clean_records(raw)
                    save_clean_json(cleaned, PROCESSED_PATH)
                    st.success(f"Fetched and processed {len(raw)} reviews from {len(product_asins)} product(s).")
                except Exception as e:
                    st.error(f"Error fetching Amazon reviews: {e}")
                    st.info("Make sure you've subscribed to the Amazon Product Reviews API on RapidAPI.")
    
    else:  # Reddit
        client_id, client_secret, user_agent = get_reddit_secrets()
        if not client_id or not client_secret:
            st.error("Reddit credentials missing. Add them to `.streamlit/secrets.toml` under `[reddit]`.")
        else:
            with st.spinner("Scraping Reddit… this may take a minute."):
                raw = scrape_reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent,
                    limit_per_query=limit,
                    since_days=days,
                )
                save_to_json(raw, RAW_PATH)
                cleaned = clean_records(raw)
                save_clean_json(cleaned, PROCESSED_PATH)
            st.success(f"Fetched and processed {len(raw)} items.")


def load_processed_df() -> pd.DataFrame:
    if not PROCESSED_PATH.exists():
        return pd.DataFrame()
    import json

    with PROCESSED_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


# Run AI Analysis
if run_analysis:
    provider, api_key, model = get_llm_secrets()
    if not api_key:
        st.error(
            "LLM API key missing. Add to `.streamlit/secrets.toml`:\n"
            "```toml\n[anthropic]\napi_key = 'your-key'\n```\n"
            "or\n```toml\n[openai]\napi_key = 'your-key'\n```"
        )
    elif not PROCESSED_PATH.exists():
        st.warning("No processed data found. Fetch Reddit data first.")
    else:
        with st.spinner("Analyzing comments with AI... This may take a few minutes."):
            try:
                analyzer = FlavorAnalyzer(
                    api_provider=provider, api_key=api_key, model=model, batch_size=batch_size
                )
                comments = load_processed_data(PROCESSED_PATH)
                
                # Analyze comments
                analysis_results = analyzer.analyze_comments(comments)
                save_analysis_results(analysis_results, ANALYSIS_PATH)
                
                # Score recommendations
                scored = score_flavor_recommendations(analysis_results, days_lookback=days)
                save_analysis_results(scored, SCORED_PATH)
                
                st.success(
                    f"Analysis complete! Processed {len(analysis_results)} comments, "
                    f"identified {len(scored)} unique flavors."
                )
                st.rerun()
            except Exception as e:
                st.error(f"Analysis failed: {e}")


# Main Dashboard Sections
df = load_processed_df()

# Load scored recommendations if available
scored_flavors = []
if SCORED_PATH.exists():
    with SCORED_PATH.open("r", encoding="utf-8") as f:
        scored_flavors = json.load(f)

# Load analysis results for timeline
analysis_results = []
if ANALYSIS_PATH.exists():
    with ANALYSIS_PATH.open("r", encoding="utf-8") as f:
        analysis_results = json.load(f)

# ============================================================================
# TREND WALL SECTION
# ============================================================================
st.header("📊 Trend Wall", divider="rainbow")

if df.empty:
    st.info("No processed data found yet. Click **Fetch latest Reddit data** in the sidebar to start.")
else:
    st.write(f"📈 **{len(df)} records** loaded from Reddit")

    if scored_flavors:
        # Word Cloud
        st.subheader("☁️ Trending Flavor Keywords")
        wordcloud_img = create_wordcloud_image(scored_flavors, max_words=50)
        if wordcloud_img:
            st.image(wordcloud_img, use_container_width=True)
        else:
            st.info("Word cloud will appear after AI analysis.")

        # Charts Row 1: Frequency and Sentiment
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Top Flavor Mentions")
            freq_chart = create_flavor_frequency_chart(scored_flavors, top_n=15)
            st.plotly_chart(freq_chart, use_container_width=True)

        with col2:
            st.subheader("😊 Overall Sentiment")
            if scored_flavors:
                total_positive = sum(f.get("positive_count", 0) for f in scored_flavors)
                total_negative = sum(f.get("negative_count", 0) for f in scored_flavors)
                total_neutral = sum(f.get("neutral_count", 0) for f in scored_flavors)
                
                sentiment_gauge = create_sentiment_gauge(total_positive, total_negative, total_neutral)
                st.plotly_chart(sentiment_gauge, use_container_width=True)
                
                # Sentiment pie chart below gauge
                sentiment_pie = create_sentiment_pie_chart(total_positive, total_negative, total_neutral)
                st.plotly_chart(sentiment_pie, use_container_width=True)

        # Timeline Chart
        if analysis_results:
            st.subheader("📅 Flavor Mentions Over Time")
            timeline_chart = create_trend_timeline(analysis_results)
            if timeline_chart.data:
                st.plotly_chart(timeline_chart, use_container_width=True)
            else:
                st.info("Timeline data will appear after processing more comments.")

        st.divider()

    # ============================================================================
    # GOLDEN CANDIDATE SECTION
    # ============================================================================
    if scored_flavors:
        st.header("🏆 Golden Candidate", divider="rainbow")
        
        golden = get_golden_candidate(scored_flavors)
        if golden:
            # Main metrics row
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🎯 Flavor", golden["flavor"].title(), delta=None)
            with col2:
                st.metric("⭐ Final Score", f"{golden['final_score']:.1f}", delta=None)
            with col3:
                st.metric("🏢 Target Brand", golden["recommended_brand"], delta=None)
            with col4:
                st.metric("💬 Mentions", golden["mention_count"], delta=None)

            # Score breakdown chart and details
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("📈 Score Breakdown")
                radar_chart = create_score_breakdown_chart(golden)
                st.plotly_chart(radar_chart, use_container_width=True)
                
                # Detailed scores
                st.write("**Component Scores:**")
                st.write(f"• Frequency: {golden['frequency_score']:.1f}/100")
                st.write(f"• Sentiment: {golden['sentiment_score']:.1f}/100")
                st.write(f"• Recency: {golden['recency_score']:.1f}/100")
                st.write(f"• Brand Fit: {golden['brand_fit_score']:.1f}/100")

            with col2:
                st.subheader("💭 Sample Supporting Comments")
                for idx, comment in enumerate(golden.get("sample_comments", [])[:5], 1):
                    st.markdown(f"**Comment {idx}:**")
                    st.text(comment[:250])
                    if idx < len(golden.get("sample_comments", [])):
                        st.divider()

            # Sentiment breakdown for golden candidate
            st.subheader("😊 Sentiment Analysis")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("👍 Positive", golden.get("positive_count", 0))
            with col2:
                st.metric("😐 Neutral", golden.get("neutral_count", 0))
            with col3:
                st.metric("👎 Negative", golden.get("negative_count", 0))

            st.divider()

    # ============================================================================
    # DECISION ENGINE SECTION
    # ============================================================================
    if scored_flavors:
        st.header("✅ Decision Engine", divider="rainbow")
        
        # Top Recommendations
        st.subheader("✅ Selected Ideas (Top Recommendations)")
        
        # Score comparison chart
        if len(scored_flavors) >= 2:
            st.write("**Score Component Comparison**")
            comparison_chart = create_score_comparison_chart(scored_flavors, top_n=5)
            st.plotly_chart(comparison_chart, use_container_width=True)
            st.divider()

        # Top 5 detailed cards
        top_5 = scored_flavors[:5]
        for idx, flavor in enumerate(top_5, 1):
            with st.expander(
                f"#{idx} {flavor['flavor'].title()} | Score: {flavor['final_score']:.1f}/100 | Brand: {flavor['recommended_brand']}",
                expanded=(idx == 1)
            ):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**📊 Metrics**")
                    st.metric("Mentions", flavor["mention_count"])
                    st.metric("Brand Fit", flavor["recommended_brand"])
                    st.write(f"**Score:** {flavor['final_score']:.1f}/100")
                
                with col2:
                    st.write("**😊 Sentiment**")
                    st.write(f"👍 Positive: {flavor['positive_count']}")
                    st.write(f"😐 Neutral: {flavor['neutral_count']}")
                    st.write(f"👎 Negative: {flavor['negative_count']}")
                
                with col3:
                    st.write("**📈 Score Components**")
                    st.write(f"Frequency: {flavor['frequency_score']:.1f}")
                    st.write(f"Sentiment: {flavor['sentiment_score']:.1f}")
                    st.write(f"Recency: {flavor['recency_score']:.1f}")
                    st.write(f"Brand Fit: {flavor['brand_fit_score']:.1f}")
                
                if flavor.get("sample_comments"):
                    st.write("**💬 Sample Comments:**")
                    for comment in flavor["sample_comments"][:3]:
                        st.text(comment[:200])
                        st.divider()

        st.divider()

        # Rejected Ideas
        rejected = get_rejected_flavors(scored_flavors, min_score=30.0)
        if rejected:
            st.subheader("❌ Rejected Ideas (Low Scores)")
            st.caption(f"Flavors scoring below 30.0 (showing top {min(10, len(rejected))} of {len(rejected)})")
            
            # Show as a compact table
            rejected_data = []
            for flavor in rejected[:10]:
                rejected_data.append({
                    "Flavor": flavor["flavor"].title(),
                    "Score": f"{flavor['final_score']:.1f}",
                    "Mentions": flavor["mention_count"],
                    "Brand": flavor.get("recommended_brand", "none"),
                })
            
            if rejected_data:
                rejected_df = pd.DataFrame(rejected_data)
                st.dataframe(rejected_df, use_container_width=True, hide_index=True)

        st.divider()

        # Brand Distribution Chart
        st.subheader("🏢 Flavor Distribution by Brand")
        brand_chart = create_brand_fit_chart(scored_flavors)
        if brand_chart.data:
            st.plotly_chart(brand_chart, use_container_width=True)
        else:
            st.info("Brand distribution will appear after analysis.")

    # ============================================================================
    # RAW DATA PREVIEW
    # ============================================================================
    st.divider()
    with st.expander("📋 Raw Data Preview (Click to expand)"):
        if not df.empty:
            st.dataframe(
                df[["type", "subreddit", "title", "body", "score", "created_at", "flavors"]].head(100),
                use_container_width=True,
                height=400,
            )
        else:
            st.info("No data to display.")

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
footer_col1, footer_col2, footer_col3 = st.columns(3)
with footer_col1:
    st.caption("**Data Source:** Reddit (r/Fitness, r/Supplements, r/nutrition, r/gainit)")
with footer_col2:
    st.caption("**AI Engine:** Claude/GPT-4 for sentiment analysis & brand fit")
with footer_col3:
    st.caption("**Last Updated:** " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))


