"""
Portfolio storage: list of tickers the analyst tracks, with their last analysis summary.
Stored in ~/.talguard/portfolio.json alongside settings.
"""

import json
import os
from datetime import datetime
from typing import Optional

import config as cfg

PORTFOLIO_PATH = os.path.join(os.path.dirname(cfg.SETTINGS_PATH), "portfolio.json")


def _load() -> list[dict]:
    if not os.path.exists(PORTFOLIO_PATH):
        return []
    try:
        with open(PORTFOLIO_PATH, "r") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(records: list[dict]):
    os.makedirs(os.path.dirname(PORTFOLIO_PATH), exist_ok=True)
    with open(PORTFOLIO_PATH, "w") as f:
        json.dump(records, f, indent=2)


def get_portfolio() -> list[dict]:
    return _load()


def add_ticker(ticker: str) -> bool:
    """Add a ticker to portfolio. Returns False if already present."""
    ticker = ticker.strip().upper()
    records = _load()
    if any(r["ticker"] == ticker for r in records):
        return False
    records.append({
        "ticker": ticker,
        "added_date": datetime.now().isoformat()[:10],
        "last_score": None,
        "last_passed": None,
        "last_company": None,
        "last_analysis_date": None,
    })
    _save(records)
    return True


def remove_ticker(ticker: str):
    ticker = ticker.strip().upper()
    records = [r for r in _load() if r["ticker"] != ticker]
    _save(records)


def update_from_result(result_dict: dict):
    """Update the portfolio entry for a ticker with the latest analysis result."""
    ticker = result_dict.get("ticker", "").upper()
    records = _load()
    for r in records:
        if r["ticker"] == ticker:
            r["last_score"] = result_dict.get("total_points")
            r["last_passed"] = result_dict.get("passed")
            r["last_company"] = result_dict.get("company_name")
            r["last_analysis_date"] = result_dict.get("analysis_date", "")[:10]
            break
    _save(records)


def is_in_portfolio(ticker: str) -> bool:
    ticker = ticker.strip().upper()
    return any(r["ticker"] == ticker for r in _load())
