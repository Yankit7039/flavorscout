"""Visualization utilities for the Flavor Scout dashboard."""

from collections import Counter
from typing import Dict, List, Any, Optional

import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import pandas as pd


def create_flavor_frequency_chart(scored_flavors: List[Dict[str, Any]], top_n: int = 20) -> go.Figure:
    """
    Create a horizontal bar chart of top flavor mentions.

    Args:
        scored_flavors: List of scored flavor recommendations
        top_n: Number of top flavors to display

    Returns:
        Plotly figure
    """
    if not scored_flavors:
        return go.Figure()

    top_flavors = scored_flavors[:top_n]
    flavors = [f["flavor"].title() for f in top_flavors]
    counts = [f["mention_count"] for f in top_flavors]
    scores = [f["final_score"] for f in top_flavors]

    fig = go.Figure()

    # Color bars by score (green = high, yellow = medium, red = low)
    colors = []
    for score in scores:
        if score >= 70:
            colors.append("#2ecc71")  # Green
        elif score >= 50:
            colors.append("#f39c12")  # Orange
        else:
            colors.append("#e74c3c")  # Red

    fig.add_trace(
        go.Bar(
            y=flavors,
            x=counts,
            orientation="h",
            marker=dict(color=colors),
            text=[f"{c} mentions" for c in counts],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Mentions: %{x}<br>Score: %{customdata:.1f}<extra></extra>",
            customdata=scores,
        )
    )

    fig.update_layout(
        title=f"Top {top_n} Flavor Mentions",
        xaxis_title="Number of Mentions",
        yaxis_title="Flavor",
        height=600,
        showlegend=False,
        margin=dict(l=150, r=20, t=50, b=20),
    )

    return fig


def create_sentiment_gauge(
    positive: int, negative: int, neutral: int
) -> go.Figure:
    """
    Create a gauge chart showing overall sentiment.

    Args:
        positive: Number of positive mentions
        negative: Number of negative mentions
        neutral: Number of neutral mentions

    Returns:
        Plotly figure
    """
    total = positive + negative + neutral
    if total == 0:
        sentiment_value = 50.0
    else:
        sentiment_value = ((positive - negative) / total) * 100 + 50  # Map to 0-100

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=sentiment_value,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Overall Sentiment"},
            delta={"reference": 50},
            gauge={
                "axis": {"range": [None, 100]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [0, 33], "color": "lightgray"},
                    {"range": [33, 66], "color": "gray"},
                    {"range": [66, 100], "color": "lightgreen"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": 90,
                },
            },
        )
    )

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig


def create_score_breakdown_chart(flavor: Dict[str, Any]) -> go.Figure:
    """
    Create a radar/spider chart showing score breakdown for a flavor.

    Args:
        flavor: Flavor dict with score components

    Returns:
        Plotly figure
    """
    categories = ["Frequency", "Sentiment", "Recency", "Brand Fit"]
    values = [
        flavor.get("frequency_score", 0),
        flavor.get("sentiment_score", 0),
        flavor.get("recency_score", 0),
        flavor.get("brand_fit_score", 0),
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            name="Scores",
            line=dict(color="rgb(46, 204, 113)"),
            fillcolor="rgba(46, 204, 113, 0.3)",
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
            )
        ),
        showlegend=False,
        title="Score Breakdown",
        height=400,
    )

    return fig


def create_sentiment_pie_chart(
    positive: int, negative: int, neutral: int
) -> go.Figure:
    """
    Create a pie chart showing sentiment distribution.

    Args:
        positive: Number of positive mentions
        negative: Number of negative mentions
        neutral: Number of neutral mentions

    Returns:
        Plotly figure
    """
    labels = ["Positive", "Neutral", "Negative"]
    values = [positive, neutral, negative]
    colors = ["#2ecc71", "#95a5a6", "#e74c3c"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker=dict(colors=colors),
                textinfo="label+percent",
            )
        ]
    )

    fig.update_layout(
        title="Sentiment Distribution",
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig


def create_wordcloud_image(
    scored_flavors: List[Dict[str, Any]], max_words: int = 50
) -> Optional[bytes]:
    """
    Generate a word cloud image from flavor data.

    Args:
        scored_flavors: List of scored flavors
        max_words: Maximum number of words in the cloud

    Returns:
        Bytes of PNG image, or None if no data
    """
    if not scored_flavors:
        return None

    # Create frequency dict from flavors and their mention counts
    word_freq = {}
    for flavor in scored_flavors:
        flavor_name = flavor["flavor"].title()
        count = flavor.get("mention_count", 1)
        word_freq[flavor_name] = count

    if not word_freq:
        return None

    # Generate word cloud
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color="white",
        max_words=max_words,
        colormap="viridis",
        relative_scaling=0.5,
    ).generate_from_frequencies(word_freq)

    # Convert to bytes
    import io

    img = wordcloud.to_image()
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    return img_bytes.getvalue()


def create_trend_timeline(analysis_results: List[Dict[str, Any]]) -> go.Figure:
    """
    Create a timeline chart showing flavor mentions over time.

    Args:
        analysis_results: List of analysis results with timestamps

    Returns:
        Plotly figure
    """
    if not analysis_results:
        return go.Figure()

    # Extract dates and flavors
    dates = []
    flavors = []

    for result in analysis_results:
        if not result.get("is_relevant", False):
            continue

        created_at = result.get("created_at", "")
        if not created_at:
            continue

        try:
            from datetime import datetime
            if isinstance(created_at, str):
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                continue
        except:
            continue

        for flavor in result.get("flavors_mentioned", []):
            dates.append(dt)
            flavors.append(flavor.lower())

    if not dates:
        return go.Figure()

    # Create DataFrame and group by date
    df = pd.DataFrame({"date": dates, "flavor": flavors})
    df["date"] = pd.to_datetime(df["date"])
    df = df.groupby([df["date"].dt.date, "flavor"]).size().reset_index(name="count")
    df["date"] = pd.to_datetime(df["date"])

    # Get top 5 flavors
    top_flavors = df.groupby("flavor")["count"].sum().nlargest(5).index.tolist()
    df_filtered = df[df["flavor"].isin(top_flavors)]

    fig = px.line(
        df_filtered,
        x="date",
        y="count",
        color="flavor",
        title="Flavor Mentions Over Time (Top 5)",
        labels={"date": "Date", "count": "Mentions", "flavor": "Flavor"},
    )

    fig.update_layout(
        height=400,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def create_brand_fit_chart(scored_flavors: List[Dict[str, Any]]) -> go.Figure:
    """
    Create a chart showing flavor distribution by brand.

    Args:
        scored_flavors: List of scored flavors

    Returns:
        Plotly figure
    """
    if not scored_flavors:
        return go.Figure()

    brand_counts = Counter()
    for flavor in scored_flavors:
        brand = flavor.get("recommended_brand", "none")
        if brand != "none":
            brand_counts[brand] += 1

    if not brand_counts:
        return go.Figure()

    brands = list(brand_counts.keys())
    counts = list(brand_counts.values())

    fig = go.Figure(
        data=[
            go.Bar(
                x=brands,
                y=counts,
                marker=dict(color=["#3498db", "#9b59b6", "#16a085"]),  # Blue, Purple, Teal
                text=counts,
                textposition="outside",
            )
        ]
    )

    fig.update_layout(
        title="Flavor Recommendations by Brand",
        xaxis_title="Brand",
        yaxis_title="Number of Flavors",
        height=400,
        showlegend=False,
    )

    return fig


def create_score_comparison_chart(scored_flavors: List[Dict[str, Any]], top_n: int = 10) -> go.Figure:
    """
    Create a grouped bar chart comparing score components for top flavors.

    Args:
        scored_flavors: List of scored flavors
        top_n: Number of top flavors to compare

    Returns:
        Plotly figure
    """
    if not scored_flavors:
        return go.Figure()

    top_flavors = scored_flavors[:top_n]
    flavors = [f["flavor"].title() for f in top_flavors]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="Frequency",
            x=flavors,
            y=[f["frequency_score"] for f in top_flavors],
            marker_color="#3498db",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Sentiment",
            x=flavors,
            y=[f["sentiment_score"] for f in top_flavors],
            marker_color="#2ecc71",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Recency",
            x=flavors,
            y=[f["recency_score"] for f in top_flavors],
            marker_color="#f39c12",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Brand Fit",
            x=flavors,
            y=[f["brand_fit_score"] for f in top_flavors],
            marker_color="#9b59b6",
        )
    )

    fig.update_layout(
        title=f"Score Component Comparison (Top {top_n})",
        xaxis_title="Flavor",
        yaxis_title="Score",
        barmode="group",
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


if __name__ == "__main__":
    print("This module provides visualization utilities for the Flavor Scout dashboard.")

