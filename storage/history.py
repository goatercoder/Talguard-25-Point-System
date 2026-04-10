"""
Local JSON-backed analysis history stored in results/history.json.
"""

import json
import os
from typing import Optional

from config import HISTORY_PATH


def _load() -> list[dict]:
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, "r") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(records: list[dict]):
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w") as f:
        json.dump(records, f, indent=2)


def save_result(result_dict: dict):
    """Append (or update) a result to history. Keyed by ticker + date."""
    records = _load()
    # Avoid duplicate: remove existing entry for same ticker+date if present
    key = (result_dict.get("ticker"), result_dict.get("analysis_date", "")[:10])
    records = [r for r in records if (r.get("ticker"), r.get("analysis_date", "")[:10]) != key]
    records.insert(0, result_dict)  # newest first
    records = records[:100]          # keep last 100
    _save(records)


def load_history() -> list[dict]:
    return _load()


def get_by_ticker(ticker: str) -> Optional[dict]:
    """Return the most recent analysis for a given ticker, or None."""
    records = _load()
    ticker = ticker.upper()
    for r in records:
        if r.get("ticker", "").upper() == ticker:
            return r
    return None
