"""
Fetches all raw yfinance data for a ticker in parallel, populating CompanyData.
All calls are individually guarded — partial failures yield INSUFFICIENT_DATA
for affected criteria rather than crashing the entire analysis.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import yfinance as yf

from core.models import CompanyData

logger = logging.getLogger(__name__)


def _safe_fetch(name: str, fn, errors: dict):
    """Run fn(), store any exception in errors[name], return result or None."""
    try:
        result = fn()
        # yfinance returns empty DataFrames for missing data — treat as None
        if hasattr(result, "empty") and result.empty:
            return None
        return result
    except Exception as exc:
        errors[name] = str(exc)
        logger.warning("yfinance fetch failed for '%s': %s", name, exc)
        return None


def fetch_all(ticker_symbol: str) -> CompanyData:
    """
    Fetch all required yfinance data for *ticker_symbol* in parallel.
    Returns a CompanyData instance; always check `.is_valid` before using.
    """
    ticker_symbol = ticker_symbol.strip().upper()
    errors: dict[str, str] = {}
    data = CompanyData(ticker_symbol=ticker_symbol, fetch_errors=errors)

    t = yf.Ticker(ticker_symbol)

    # Define each fetch as a (field_name, callable) pair
    tasks = {
        "info":                 lambda: t.info,
        "income_stmt":          lambda: t.income_stmt,
        "balance_sheet":        lambda: t.balance_sheet,
        "cash_flow":            lambda: t.cash_flow,
        "dividends":            lambda: t.dividends,
        "price_history":        lambda: t.history(period="10y"),
        "insider_transactions": lambda: t.insider_transactions,
    }

    results: dict[str, object] = {}

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {
            pool.submit(_safe_fetch, name, fn, errors): name
            for name, fn in tasks.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            results[name] = future.result()

    data.info                 = results.get("info") or {}
    data.income_stmt          = results.get("income_stmt")
    data.balance_sheet        = results.get("balance_sheet")
    data.cash_flow            = results.get("cash_flow")
    data.dividends            = results.get("dividends")
    data.price_history        = results.get("price_history")
    data.insider_transactions = results.get("insider_transactions")
    data.fetch_timestamp      = datetime.now()

    if not data.is_valid:
        errors["ticker"] = f"Ticker '{ticker_symbol}' not found or returned no data."

    return data
