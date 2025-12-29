"""
Amazon Product Reviews Scraper using RapidAPI.

This module provides an alternative to Reddit scraping that:
- Requires no approval (just RapidAPI signup)
- Allows commercial use
- Provides highly relevant flavor feedback from product reviews
- Can be set up in 15-30 minutes
"""

import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests


@dataclass
class ReviewItem:
    """Compatible with RedditItem structure for seamless integration."""
    id: str
    type: str  # "review"
    subreddit: str  # "amazon" or "flipkart" etc.
    title: Optional[str]
    body: str
    score: int  # Rating (1-5)
    created_utc: float
    created_at: str
    url: Optional[str]
    product_name: Optional[str] = None
    helpful_votes: int = 0


def scrape_amazon_reviews_rapidapi(
    product_ids: List[str],
    api_key: str,
    max_reviews_per_product: int = 100,
    delay_between_requests: float = 1.0,
) -> List[Dict[str, Any]]:
    """
    Scrape Amazon product reviews using RapidAPI.
    
    Args:
        product_ids: List of Amazon ASINs (e.g., ["B08XYZ123", "B09ABC456"])
        api_key: Your RapidAPI key
        max_reviews_per_product: Maximum reviews to fetch per product
        delay_between_requests: Seconds to wait between API calls (respect rate limits)
    
    Returns:
        List of review dictionaries compatible with Flavor Scout format
    
    Example:
        >>> reviews = scrape_amazon_reviews_rapidapi(
        ...     product_ids=["B08XYZ123"],
        ...     api_key="your_rapidapi_key",
        ...     max_reviews_per_product=50
        ... )
    """
    url = "https://amazon-product-reviews-keywords.p.rapidapi.com/product/reviews"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "amazon-product-reviews-keywords.p.rapidapi.com"
    }
    
    all_reviews: List[ReviewItem] = []
    
    for idx, asin in enumerate(product_ids):
        if idx > 0:
            time.sleep(delay_between_requests)  # Rate limiting
        
        params = {"asin": asin, "country": "IN"}  # India for HealthKart products
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract product name if available
            product_name = data.get("product", {}).get("title", "Unknown Product")
            
            # Process reviews
            reviews = data.get("reviews", [])[:max_reviews_per_product]
            
            for review in reviews:
                # Parse date
                review_date = review.get("date", "")
                created_utc = _parse_review_date(review_date)
                
                review_item = ReviewItem(
                    id=f"amazon_{asin}_{review.get('id', '')}",
                    type="review",
                    subreddit="amazon",
                    title=review.get("title", ""),
                    body=review.get("text", ""),
                    score=int(review.get("rating", 0)),
                    created_utc=created_utc,
                    created_at=review_date,
                    url=f"https://www.amazon.in/dp/{asin}",
                    product_name=product_name,
                    helpful_votes=int(review.get("helpful", 0)),
                )
                all_reviews.append(review_item)
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching reviews for ASIN {asin}: {e}")
            continue
        except Exception as e:
            print(f"Unexpected error for ASIN {asin}: {e}")
            continue
    
    return [asdict(item) for item in all_reviews]


def _parse_review_date(date_str: str) -> float:
    """Parse review date string to UTC timestamp."""
    try:
        # Try common date formats
        formats = [
            "%Y-%m-%d",
            "%d %B %Y",
            "%B %d, %Y",
            "%Y-%m-%d %H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.timestamp()
            except ValueError:
                continue
        
        # Fallback to current time
        return datetime.now(timezone.utc).timestamp()
    except Exception:
        return datetime.now(timezone.utc).timestamp()


def scrape_amazon_reviews_simple(
    product_ids: List[str],
    api_key: str,
    max_reviews: int = 100,
) -> List[Dict[str, Any]]:
    """
    Simplified wrapper for scraping Amazon reviews.
    
    This is a convenience function that uses sensible defaults.
    """
    return scrape_amazon_reviews_rapidapi(
        product_ids=product_ids,
        api_key=api_key,
        max_reviews_per_product=max_reviews,
        delay_between_requests=1.0,
    )


# Example HealthKart/MuscleBlaze product ASINs (you'll need to find actual ones)
EXAMPLE_PRODUCT_ASINS = [
    # Add real Amazon ASINs here
    # Example format: "B08XYZ123" (found in Amazon product URLs)
    # "B08XYZ123",  # MuscleBlaze Whey Protein - Chocolate
    # "B09ABC456",  # MuscleBlaze Whey Protein - Vanilla
]


def main() -> None:
    """CLI entry point for manual testing."""
    print(
        "Amazon Reviews Scraper\n"
        "=====================\n\n"
        "To use this module:\n"
        "1. Sign up at https://rapidapi.com\n"
        "2. Subscribe to 'Amazon Product Reviews Keywords' API\n"
        "3. Get your API key from RapidAPI dashboard\n"
        "4. Add to .streamlit/secrets.toml:\n"
        "   [rapidapi]\n"
        "   api_key = 'your_key_here'\n\n"
        "5. Find Amazon ASINs for products you want to analyze\n"
        "   (ASIN is in the product URL: amazon.in/dp/ASIN_HERE)\n\n"
        "6. Import and use:\n"
        "   from modules.scraper_amazon import scrape_amazon_reviews_simple\n"
        "   reviews = scrape_amazon_reviews_simple(\n"
        "       product_ids=['B08XYZ123'],\n"
        "       api_key='your_key'\n"
        "   )"
    )


if __name__ == "__main__":
    main()

