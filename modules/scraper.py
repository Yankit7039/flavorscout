import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Dict, Any, Optional

import praw


DEFAULT_SUBREDDITS = ["Fitness", "Supplements", "nutrition", "gainit"]
DEFAULT_SEARCH_QUERIES = [
    "protein flavor",
    "whey flavor",
    "supplement taste",
    "protein powder taste",
]


@dataclass
class RedditItem:
    id: str
    type: str  # "post" or "comment"
    subreddit: str
    title: Optional[str]
    body: str
    score: int
    created_utc: float
    created_at: str
    url: Optional[str]


def _build_reddit_client(
    client_id: str,
    client_secret: str,
    user_agent: str = "flavor-scout-app",
) -> praw.Reddit:
    """Create a read-only Reddit client."""
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )
    reddit.read_only = True
    return reddit


def _iter_search_results(
    reddit: praw.Reddit,
    subreddits: Iterable[str],
    queries: Iterable[str],
    limit_per_query: int = 200,
) -> Iterable[praw.models.Submission]:
    for sub in subreddits:
        subreddit = reddit.subreddit(sub)
        for query in queries:
            for submission in subreddit.search(
                query=query, sort="new", time_filter="year", limit=limit_per_query
            ):
                yield submission


def _flatten_items(
    submissions: Iterable[praw.models.Submission],
    since_days: int = 90,
    include_comments: bool = True,
) -> List[RedditItem]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    items: List[RedditItem] = []
    seen_ids: set[str] = set()

    for submission in submissions:
        created_dt = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
        if created_dt < cutoff:
            continue

        post_id = f"post_{submission.id}"
        if post_id not in seen_ids:
            seen_ids.add(post_id)
            items.append(
                RedditItem(
                    id=post_id,
                    type="post",
                    subreddit=str(submission.subreddit),
                    title=submission.title,
                    body=submission.selftext or "",
                    score=submission.score,
                    created_utc=submission.created_utc,
                    created_at=created_dt.isoformat(),
                    url=submission.url,
                )
            )

        if not include_comments:
            continue

        submission.comments.replace_more(limit=0)
        for comment in submission.comments.list():
            if not getattr(comment, "body", None):
                continue
            c_created_dt = datetime.fromtimestamp(comment.created_utc, tz=timezone.utc)
            if c_created_dt < cutoff:
                continue

            comment_id = f"comment_{comment.id}"
            if comment_id in seen_ids:
                continue

            seen_ids.add(comment_id)
            items.append(
                RedditItem(
                    id=comment_id,
                    type="comment",
                    subreddit=str(submission.subreddit),
                    title=submission.title,
                    body=comment.body,
                    score=comment.score,
                    created_utc=comment.created_utc,
                    created_at=c_created_dt.isoformat(),
                    url=f"https://www.reddit.com{comment.permalink}",
                )
            )

    return items


def scrape_reddit(
    client_id: str,
    client_secret: str,
    user_agent: str = "flavor-scout-app",
    subreddits: Optional[Iterable[str]] = None,
    queries: Optional[Iterable[str]] = None,
    limit_per_query: int = 200,
    since_days: int = 90,
    include_comments: bool = True,
) -> List[Dict[str, Any]]:
    """High-level helper to fetch Reddit posts/comments for flavor analysis."""
    subreddits = subreddits or DEFAULT_SUBREDDITS
    queries = queries or DEFAULT_SEARCH_QUERIES

    reddit = _build_reddit_client(client_id, client_secret, user_agent)
    submissions = _iter_search_results(
        reddit, subreddits=subreddits, queries=queries, limit_per_query=limit_per_query
    )
    items = _flatten_items(
        submissions, since_days=since_days, include_comments=include_comments
    )
    return [asdict(item) for item in items]


def save_to_json(data: List[Dict[str, Any]], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    """CLI entry point for manual testing.

    Expects environment variables or a `.streamlit/secrets.toml` driven runner.
    For quick local tests, you can hard-code credentials here (but never commit them).
    """
    print(
        "This module is intended to be used from the Streamlit app or other Python code.\n"
        "Import and call `scrape_reddit` with your Reddit credentials."
    )


if __name__ == "__main__":
    main()




