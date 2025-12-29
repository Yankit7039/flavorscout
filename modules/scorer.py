"""Scoring engine for ranking flavor recommendations."""

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional


def calculate_frequency_score(mention_count: int, max_mentions: int) -> float:
    """
    Calculate frequency score (0-100) based on how often a flavor is mentioned.

    Args:
        mention_count: Number of times flavor was mentioned
        max_mentions: Maximum mentions across all flavors (for normalization)

    Returns:
        Score from 0-100
    """
    if max_mentions == 0:
        return 0.0
    # Logarithmic scaling to avoid over-weighting very popular flavors
    import math
    normalized = mention_count / max_mentions
    return min(100.0, 50.0 + 50.0 * math.log1p(normalized * 9))  # log1p(x*9) maps [0,1] to [0,2.3]


def calculate_sentiment_score(
    positive: int, negative: int, neutral: int
) -> float:
    """
    Calculate sentiment score (0-100) based on positive vs negative mentions.

    Args:
        positive: Number of positive mentions
        negative: Number of negative mentions
        neutral: Number of neutral mentions

    Returns:
        Score from 0-100 (higher = more positive)
    """
    total = positive + negative + neutral
    if total == 0:
        return 50.0  # Neutral default

    # Weight: positive = +1, negative = -1, neutral = 0
    sentiment_value = (positive - negative) / total
    # Map [-1, 1] to [0, 100]
    return 50.0 + (sentiment_value * 50.0)


def calculate_recency_score(
    mentions: List[Dict[str, Any]], days_lookback: int = 90
) -> float:
    """
    Calculate recency score (0-100) based on how recent the mentions are.

    Args:
        mentions: List of mention dicts with 'created_at' or 'created_utc'
        days_lookback: Total lookback window in days

    Returns:
        Score from 0-100 (higher = more recent)
    """
    if not mentions:
        return 0.0

    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - (days_lookback * 24 * 3600)

    recent_count = 0
    for mention in mentions:
        created = mention.get("created_utc") or mention.get("created_at")
        if isinstance(created, str):
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                created = created_dt.timestamp()
            except:
                continue
        if isinstance(created, (int, float)) and created >= cutoff:
            # More recent = higher weight
            days_ago = (now.timestamp() - created) / (24 * 3600)
            weight = max(0, 1.0 - (days_ago / days_lookback))
            recent_count += weight

    # Normalize to 0-100
    max_possible = len(mentions)
    if max_possible == 0:
        return 0.0
    return min(100.0, (recent_count / max_possible) * 100.0)


def calculate_brand_fit_score(brand: str, brand_fit_counts: Dict[str, int]) -> float:
    """
    Calculate brand fit score (0-100) based on how well flavor aligns with brand.

    Args:
        brand: Brand name (MuscleBlaze, HK Vitals, TrueBasics)
        brand_fit_counts: Dict mapping brand names to mention counts

    Returns:
        Score from 0-100
    """
    total = sum(brand_fit_counts.values())
    if total == 0:
        return 0.0

    brand_count = brand_fit_counts.get(brand, 0)
    return (brand_count / total) * 100.0


def calculate_final_score(
    frequency_score: float,
    sentiment_score: float,
    recency_score: float,
    brand_fit_score: float,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Calculate weighted final score (0-100).

    Args:
        frequency_score: Frequency component (0-100)
        sentiment_score: Sentiment component (0-100)
        recency_score: Recency component (0-100)
        brand_fit_score: Brand fit component (0-100)
        weights: Optional dict with keys 'frequency', 'sentiment', 'recency', 'brand_fit'
                 Defaults to equal weights (0.25 each)

    Returns:
        Final weighted score (0-100)
    """
    if weights is None:
        weights = {
            "frequency": 0.30,
            "sentiment": 0.30,
            "recency": 0.20,
            "brand_fit": 0.20,
        }

    total_weight = sum(weights.values())
    if total_weight == 0:
        return 0.0

    # Normalize weights
    normalized_weights = {k: v / total_weight for k, v in weights.items()}

    final = (
        frequency_score * normalized_weights.get("frequency", 0.25)
        + sentiment_score * normalized_weights.get("sentiment", 0.25)
        + recency_score * normalized_weights.get("recency", 0.25)
        + brand_fit_score * normalized_weights.get("brand_fit", 0.25)
    )

    return round(final, 2)


def score_flavor_recommendations(
    analysis_results: List[Dict[str, Any]],
    days_lookback: int = 90,
    weights: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """
    Score and rank flavor recommendations from AI analysis results.

    Args:
        analysis_results: List of analysis dicts from FlavorAnalyzer
        days_lookback: Lookback window for recency calculation
        weights: Optional scoring weights

    Returns:
        List of scored flavor recommendations, sorted by final_score (descending)
    """
    # Group by flavor
    flavor_data: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "flavor": "",
            "mentions": [],
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "brand_fit_counts": Counter(),
            "sample_comments": [],
        }
    )

    for result in analysis_results:
        if not result.get("is_relevant", False):
            continue

        flavors = result.get("flavors_mentioned", [])
        if not flavors:
            continue

        sentiment = result.get("sentiment", "neutral").lower()
        brand_fit = result.get("brand_fit", "none")
        comment_text = result.get("comment_text", "")[:200]

        for flavor in flavors:
            flavor_lower = flavor.lower().strip()
            if not flavor_lower:
                continue

            data = flavor_data[flavor_lower]
            data["flavor"] = flavor_lower

            # Track mention
            mention_info = {
                "comment_id": result.get("comment_id", ""),
                "created_at": result.get("created_at", ""),
                "created_utc": result.get("created_utc", 0),
                "sentiment": sentiment,
            }
            data["mentions"].append(mention_info)

            # Count sentiment
            if sentiment == "positive":
                data["positive_count"] += 1
            elif sentiment == "negative":
                data["negative_count"] += 1
            else:
                data["neutral_count"] += 1

            # Track brand fit
            if brand_fit and brand_fit != "none":
                data["brand_fit_counts"][brand_fit] += 1

            # Collect sample comments (up to 5 per flavor)
            if len(data["sample_comments"]) < 5 and comment_text:
                data["sample_comments"].append(comment_text)

    # Calculate scores for each flavor
    scored_flavors: List[Dict[str, Any]] = []
    max_mentions = max(
        (len(data["mentions"]) for data in flavor_data.values()), default=1
    )

    for flavor, data in flavor_data.items():
        mention_count = len(data["mentions"])

        # Calculate component scores
        freq_score = calculate_frequency_score(mention_count, max_mentions)
        sent_score = calculate_sentiment_score(
            data["positive_count"],
            data["negative_count"],
            data["neutral_count"],
        )
        recency_score = calculate_recency_score(data["mentions"], days_lookback)

        # Determine best brand fit
        brand_fit_counts = dict(data["brand_fit_counts"])
        if brand_fit_counts:
            best_brand = max(brand_fit_counts.items(), key=lambda x: x[1])[0]
            brand_fit_score = calculate_brand_fit_score(best_brand, brand_fit_counts)
        else:
            best_brand = "none"
            brand_fit_score = 0.0

        # Calculate final score
        final_score = calculate_final_score(
            freq_score, sent_score, recency_score, brand_fit_score, weights
        )

        scored_flavors.append(
            {
                "flavor": data["flavor"],
                "final_score": final_score,
                "frequency_score": round(freq_score, 2),
                "sentiment_score": round(sent_score, 2),
                "recency_score": round(recency_score, 2),
                "brand_fit_score": round(brand_fit_score, 2),
                "mention_count": mention_count,
                "positive_count": data["positive_count"],
                "negative_count": data["negative_count"],
                "neutral_count": data["neutral_count"],
                "recommended_brand": best_brand,
                "brand_fit_breakdown": brand_fit_counts,
                "sample_comments": data["sample_comments"][:3],  # Top 3 samples
            }
        )

    # Sort by final_score descending
    scored_flavors.sort(key=lambda x: x["final_score"], reverse=True)

    return scored_flavors


def get_golden_candidate(scored_flavors: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Get the top-ranked flavor recommendation (Golden Candidate).

    Args:
        scored_flavors: List of scored flavors (should be pre-sorted)

    Returns:
        Top flavor dict or None if list is empty
    """
    if not scored_flavors:
        return None

    top = scored_flavors[0].copy()
    top["rank"] = 1
    return top


def get_rejected_flavors(
    scored_flavors: List[Dict[str, Any]], min_score: float = 30.0
) -> List[Dict[str, Any]]:
    """
    Get flavors that scored below threshold (rejected ideas).

    Args:
        scored_flavors: List of scored flavors
        min_score: Minimum score threshold

    Returns:
        List of rejected flavors (sorted by score ascending)
    """
    rejected = [f for f in scored_flavors if f["final_score"] < min_score]
    rejected.sort(key=lambda x: x["final_score"])
    return rejected


if __name__ == "__main__":
    # Example usage
    print(
        "This module is intended to be used from the Streamlit app.\n"
        "Import score_flavor_recommendations and use it with AI analysis results."
    )



