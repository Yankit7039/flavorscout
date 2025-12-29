import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Any

FLAVOR_REGEX = re.compile(
    r"\b("
    r"chocolate|vanilla|strawberry|mango|banana|cookies and cream|cookie(?:s)? n cream|"
    r"coffee|mocha|kesar|paan|kulfi|rasmalai|butterscotch|blueberry|mint|peanut butter|"
    r"salted caramel|caramel|oreo|biscuit|thandai|rose|lychee|orange|lemon|pineapple"
    r")\b",
    flags=re.IGNORECASE,
)


def load_json(path: str | Path) -> List[Dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def is_potential_spam(text: str) -> bool:
    """Very lightweight spam / low-signal heuristic filter."""
    text = text.strip()
    if len(text) < 10:
        return True
    if text.lower() in {"[deleted]", "[removed]"}:
        return True
    return False


def extract_flavors(text: str) -> List[str]:
    return [m.group(0).lower() for m in FLAVOR_REGEX.finditer(text)]


def clean_records(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen_ids = set()
    cleaned: List[Dict[str, Any]] = []

    for rec in records:
        rec_id = rec.get("id")
        if not rec_id or rec_id in seen_ids:
            continue
        seen_ids.add(rec_id)

        body = rec.get("body") or ""
        if is_potential_spam(body):
            continue

        flavors = extract_flavors(body)
        if not flavors:
            # keep non-flavor comments too; AI can still mine them
            flavors = []

        rec_clean = {**rec, "flavors": flavors}
        cleaned.append(rec_clean)

    return cleaned


def summarize_flavors(cleaned_records: Iterable[Dict[str, Any]]) -> Counter:
    counter: Counter = Counter()
    for rec in cleaned_records:
        for fl in rec.get("flavors", []):
            counter[fl] += 1
    return counter


def save_json(data: Any, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)





