"""AI-powered analysis engine for flavor recommendations."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from prompts.ai_prompts import (
    BATCH_ANALYSIS_PROMPT_TEMPLATE,
    FLAVOR_ANALYSIS_USER_PROMPT_TEMPLATE,
    FLAVOR_EXTRACTION_SYSTEM_PROMPT,
    GOLDEN_CANDIDATE_PROMPT_TEMPLATE,
)

# Default batch size for API calls (to avoid token limits)
DEFAULT_BATCH_SIZE = 20


class FlavorAnalyzer:
    """Analyzes Reddit comments using LLM to extract flavor insights."""

    def __init__(
        self,
        api_provider: str = "anthropic",  # "anthropic" or "openai"
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ):
        """
        Initialize the analyzer.

        Args:
            api_provider: "anthropic" (Claude) or "openai" (GPT)
            api_key: API key (if None, tries to read from env vars)
            model: Model name (defaults to claude-3-5-sonnet-20241022 or gpt-4)
            batch_size: Number of comments to analyze per API call
        """
        self.api_provider = api_provider.lower()
        self.batch_size = batch_size

        if api_key is None:
            if self.api_provider == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
            elif self.api_provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                f"API key not provided. Set {api_provider.upper()}_API_KEY env var or pass api_key."
            )

        if self.api_provider == "anthropic":
            if Anthropic is None:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
            self.client = Anthropic(api_key=api_key)
            self.model = model or "claude-3-5-sonnet-20241022"
        elif self.api_provider == "openai":
            if OpenAI is None:
                raise ImportError("openai package not installed. Run: pip install openai")
            self.client = OpenAI(api_key=api_key)
            self.model = model or "gpt-4"
        else:
            raise ValueError(f"Unsupported API provider: {api_provider}")

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Make API call to LLM and return response text."""
        try:
            if self.api_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                return response.content[0].text
            else:  # OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                )
                return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"LLM API call failed: {e}")

    def _parse_json_response(self, text: str) -> Any:
        """Extract JSON from LLM response (handles markdown code blocks)."""
        text = text.strip()
        # Remove markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Find the closing ```
            end_idx = None
            for i, line in enumerate(lines[1:], 1):
                if line.strip().startswith("```"):
                    end_idx = i
                    break
            if end_idx:
                text = "\n".join(lines[1:end_idx])
            else:
                text = "\n".join(lines[1:])
        # Try to find JSON object/array
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1:
            start = text.find("[")
            end = text.rfind("]") + 1
        if start >= 0 and end > start:
            text = text[start:end]
        return json.loads(text)

    def analyze_comments(
        self, comments: List[Dict[str, Any]], batch_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze a list of comments and extract flavor insights.

        Args:
            comments: List of comment dicts with at least 'id' and 'body' fields
            batch_size: Override default batch size

        Returns:
            List of analysis results with flavor mentions, sentiment, brand fit, etc.
        """
        batch_size = batch_size or self.batch_size
        all_results: List[Dict[str, Any]] = []

        for i in range(0, len(comments), batch_size):
            batch = comments[i : i + batch_size]
            comments_text = self._format_comments_for_prompt(batch)
            user_prompt = FLAVOR_ANALYSIS_USER_PROMPT_TEMPLATE.format(
                comments_text=comments_text
            )

            try:
                response_text = self._call_llm(
                    FLAVOR_EXTRACTION_SYSTEM_PROMPT, user_prompt
                )
                batch_results = self._parse_json_response(response_text)
                if not isinstance(batch_results, list):
                    # If LLM returns a single object, wrap it
                    batch_results = [batch_results]
                
                # Create a mapping of comment_id to original comment
                comment_map = {comment.get("id", f"comment_{i}"): comment for i, comment in enumerate(batch)}
                
                # Merge LLM analysis with original comment metadata
                for result in batch_results:
                    comment_id = result.get("comment_id", "")
                    original = comment_map.get(comment_id)
                    if original:
                        # Preserve original metadata for scoring
                        result["created_at"] = original.get("created_at", "")
                        result["created_utc"] = original.get("created_utc", 0)
                        result["subreddit"] = original.get("subreddit", "")
                        result["score"] = original.get("score", 0)
                
                all_results.extend(batch_results)
            except Exception as e:
                print(f"Warning: Failed to analyze batch {i//batch_size + 1}: {e}")
                continue

        return all_results

    def _format_comments_for_prompt(self, comments: List[Dict[str, Any]]) -> str:
        """Format comments into a readable text block for the prompt."""
        lines = []
        for idx, comment in enumerate(comments, 1):
            comment_id = comment.get("id", f"comment_{idx}")
            body = comment.get("body", "").strip()[:500]  # Truncate long comments
            title = comment.get("title", "")
            subreddit = comment.get("subreddit", "")
            lines.append(
                f"[{idx}] ID: {comment_id}\n"
                f"Subreddit: r/{subreddit}\n"
                f"Title: {title}\n"
                f"Text: {body}\n"
            )
        return "\n".join(lines)

    def analyze_batch_summary(
        self, comments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze a batch of comments and return a summary with unique flavors.

        Args:
            comments: List of comment dicts

        Returns:
            Dict with unique_flavors and top_recommendations
        """
        comments_text = self._format_comments_for_prompt(comments[:50])  # Limit to 50 for summary
        user_prompt = BATCH_ANALYSIS_PROMPT_TEMPLATE.format(
            count=len(comments), comments_text=comments_text
        )

        response_text = self._call_llm(
            FLAVOR_EXTRACTION_SYSTEM_PROMPT, user_prompt
        )
        return self._parse_json_response(response_text)

    def identify_golden_candidate(
        self, flavor_analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Identify the top recommendation (Golden Candidate) from analyzed data.

        Args:
            flavor_analysis_data: Dict containing flavor summaries, scores, etc.

        Returns:
            Dict with golden candidate details
        """
        # Format the data as JSON string for the prompt
        data_text = json.dumps(flavor_analysis_data, indent=2)
        user_prompt = GOLDEN_CANDIDATE_PROMPT_TEMPLATE.format(flavor_data=data_text)

        response_text = self._call_llm(
            FLAVOR_EXTRACTION_SYSTEM_PROMPT, user_prompt
        )
        return self._parse_json_response(response_text)


def load_processed_data(path: str | Path) -> List[Dict[str, Any]]:
    """Helper to load processed Reddit data."""
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def save_analysis_results(results: Any, path: str | Path) -> None:
    """Helper to save analysis results to JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # Example usage
    print(
        "This module is intended to be used from the Streamlit app.\n"
        "Import FlavorAnalyzer and use it with your API keys."
    )

