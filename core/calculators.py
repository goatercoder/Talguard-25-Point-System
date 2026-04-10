"""
Derived metric calculations built on top of CompanyData.
Each function returns a typed dict with the computed value(s) and a 'source' string.
All functions handle None / missing data gracefully — callers check for None results.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

from core.models import CompanyData

logger = logging.getLogger(__name__)


def _safe_float(val) -> Optional[float]:
    """Convert val to float; return None if impossible."""
    try:
        f = float(val)
        return None if (np.isnan(f) or np.isinf(f)) else f
    except Exception:
        return None


# ── Dividend helpers ────────────────────────────────────────────────────────

def calc_dividend_consistency(data: CompanyData) -> dict:
    """
    Check 5 years of annual dividend totals for consistency and no cuts.
    Returns:
        consistent (bool): True if dividends paid every year with no cuts
        years_checked (int)
        annual_totals (dict[int, float])
        no_dividends (bool): True if company never paid dividends
    """
    divs = data.dividends
    if divs is None or len(divs) == 0:
        return {"consistent": False, "years_checked": 0, "annual_totals": {}, "no_dividends": True}

    # Normalize timezone
    if hasattr(divs.index, "tz") and divs.index.tz is not None:
        divs = divs.tz_localize(None)

    annual = divs.resample("YE").sum()
    annual = annual[annual > 0]

    if len(annual) == 0:
        return {"consistent": False, "years_checked": 0, "annual_totals": {}, "no_dividends": True}

    # Take last 5 full years
    last_5 = annual.iloc[-5:] if len(annual) >= 5 else annual
    totals = {int(idx.year): float(v) for idx, v in last_5.items()}

    if len(last_5) < 2:
        return {"consistent": False, "years_checked": len(last_5), "annual_totals": totals, "no_dividends": False}

    values = list(last_5.values)
    years = list(last_5.index)

    # Check for full coverage (no gap years)
    expected_years = set(range(int(years[0].year), int(years[-1].year) + 1))
    actual_years = {int(y.year) for y in years}
    no_gaps = expected_years == actual_years

    # Check no cuts (each year >= prior year)
    no_cuts = all(values[i] >= values[i - 1] for i in range(1, len(values)))

    return {
        "consistent": no_gaps and no_cuts,
        "years_checked": len(last_5),
        "annual_totals": totals,
        "no_dividends": False,
        "no_gaps": no_gaps,
        "no_cuts": no_cuts,
    }


def calc_dividend_growth_rate(data: CompanyData) -> Optional[float]:
    """
    Returns most recent YoY annual dividend growth rate as a percentage.
    e.g. 12.5 means +12.5% growth. Returns None if insufficient data.
    """
    divs = data.dividends
    if divs is None or len(divs) == 0:
        return None

    if hasattr(divs.index, "tz") and divs.index.tz is not None:
        divs = divs.tz_localize(None)

    annual = divs.resample("YE").sum()
    annual = annual[annual > 0]

    if len(annual) < 2:
        return None

    latest = float(annual.iloc[-1])
    prior = float(annual.iloc[-2])

    if prior == 0:
        return None

    return (latest - prior) / prior * 100.0


# ── Share buyback ────────────────────────────────────────────────────────────

def calc_buyback_pct(data: CompanyData) -> Optional[float]:
    """
    Returns YoY share reduction as a positive percentage if buybacks occurred,
    negative if shares increased (dilution). None if data unavailable.
    """
    bs = data.balance_sheet
    if bs is None:
        return None

    # Try several row names yfinance uses across versions
    share_rows = [
        "Ordinary Shares Number",
        "Share Issued",
        "Common Stock Shares Outstanding",
    ]

    shares_row = None
    for row in share_rows:
        if row in bs.index:
            shares_row = bs.loc[row]
            break

    if shares_row is None:
        # Fallback: use info sharesOutstanding for current + balance sheet for prior
        current = _safe_float(data.info.get("sharesOutstanding"))
        if current is None:
            return None
        # No prior year data available without balance sheet row
        return None

    # columns are sorted newest → oldest in yfinance
    cols = shares_row.dropna()
    if len(cols) < 2:
        return None

    shares_now = _safe_float(cols.iloc[0])
    shares_prior = _safe_float(cols.iloc[1])

    if shares_now is None or shares_prior is None or shares_prior == 0:
        return None

    return (shares_prior - shares_now) / shares_prior * 100.0


# ── Free Cash Flow ───────────────────────────────────────────────────────────

def calc_fcf_history(data: CompanyData) -> Optional[list[float]]:
    """
    Returns list of annual FCF values (up to 4 years), newest first.
    FCF = Operating Cash Flow + Capital Expenditure (capex is negative in yfinance).
    Returns None if cash flow statement unavailable.
    """
    cf = data.cash_flow
    if cf is None:
        return None

    # Try common row names
    ocf_rows = ["Operating Cash Flow", "Cash Flow From Operations", "Cash From Operating Activities"]
    capex_rows = ["Capital Expenditure", "Purchase Of PPE", "Purchases of property, plant and equipment"]

    ocf_row = next((r for r in ocf_rows if r in cf.index), None)
    capex_row = next((r for r in capex_rows if r in cf.index), None)

    if ocf_row is None:
        return None

    ocf_series = cf.loc[ocf_row].dropna()

    if capex_row is not None:
        capex_series = cf.loc[capex_row].reindex(ocf_series.index).fillna(0)
        fcf_series = ocf_series + capex_series  # capex is already negative
    else:
        fcf_series = ocf_series  # Use OCF as proxy if capex missing

    return [_safe_float(v) for v in fcf_series.values]


# ── Historical P/E ───────────────────────────────────────────────────────────

def calc_historical_pe(data: CompanyData) -> Optional[dict]:
    """
    Approximates historical P/E using up to 4 years of annual financials.
    Returns:
        avg_pe (float): mean historical P/E
        current_pe (float): trailing P/E from yfinance info
        years_available (int)
        current_below_avg (bool)
    Returns None if insufficient data.
    """
    price_hist = data.price_history
    income = data.income_stmt
    bs = data.balance_sheet

    current_pe = _safe_float(data.info.get("trailingPE"))
    if current_pe is None or current_pe <= 0:
        return None

    if income is None or bs is None or price_hist is None:
        return None

    # Find Net Income row
    ni_rows = ["Net Income", "Net Income Common Stockholders", "Net Income Applicable To Common Shares"]
    ni_row = next((r for r in ni_rows if r in income.index), None)
    if ni_row is None:
        return None

    # Find shares row
    share_rows = ["Ordinary Shares Number", "Share Issued", "Common Stock Shares Outstanding"]
    sh_row = next((r for r in share_rows if r in bs.index), None)

    ni_series = income.loc[ni_row].dropna()

    # Year-end closing prices
    if hasattr(price_hist.index, "tz") and price_hist.index.tz is not None:
        price_hist = price_hist.copy()
        price_hist.index = price_hist.index.tz_localize(None)

    annual_prices = price_hist["Close"].resample("YE").last()

    historical_pes = []
    for col in ni_series.index:
        year = col.year
        ni = _safe_float(ni_series[col])
        if ni is None or ni <= 0:
            continue

        # Shares for EPS
        if sh_row is not None and col in bs.columns:
            shares = _safe_float(bs.loc[sh_row, col])
        else:
            shares = _safe_float(data.info.get("sharesOutstanding"))

        if shares is None or shares == 0:
            continue

        eps = ni / shares

        # Year-end price
        year_prices = annual_prices[annual_prices.index.year == year]
        if year_prices.empty:
            continue

        price = _safe_float(year_prices.iloc[-1])
        if price is None or price <= 0:
            continue

        historical_pes.append(price / eps)

    if not historical_pes:
        return None

    avg_pe = float(np.mean(historical_pes))

    return {
        "avg_pe": avg_pe,
        "current_pe": current_pe,
        "years_available": len(historical_pes),
        "current_below_avg": current_pe < avg_pe,
    }


# ── Historical PEG ───────────────────────────────────────────────────────────

def get_current_peg(info: dict) -> Optional[float]:
    """
    Return the best available current PEG ratio from yfinance info.
    Tries pegRatio → trailingPegRatio → trailingPE / (earningsGrowth * 100).
    """
    for field in ("pegRatio", "trailingPegRatio"):
        val = _safe_float(info.get(field))
        if val is not None and val > 0:
            return val
    # Calculate from trailing P/E and earnings growth as last resort
    pe = _safe_float(info.get("trailingPE"))
    growth = _safe_float(info.get("earningsGrowth"))  # decimal, e.g. 0.183 = 18.3%
    if pe is not None and growth is not None and pe > 0 and growth > 0:
        return pe / (growth * 100)
    return None


def calc_historical_peg(data: CompanyData) -> Optional[dict]:
    """
    Approximates historical PEG using the best available current PEG vs a calculated
    multi-year average PEG based on EPS growth. Returns None if insufficient data.
    """
    current_peg = get_current_peg(data.info)
    if current_peg is None or current_peg <= 0:
        return None

    income = data.income_stmt
    if income is None:
        return None

    ni_rows = ["Net Income", "Net Income Common Stockholders", "Net Income Applicable To Common Shares"]
    ni_row = next((r for r in ni_rows if r in income.index), None)
    if ni_row is None:
        return None

    ni_series = income.loc[ni_row].dropna()
    if len(ni_series) < 3:
        return None

    # EPS growth rates per year
    bs = data.balance_sheet
    share_rows = ["Ordinary Shares Number", "Share Issued"]
    sh_row = next((r for r in share_rows if bs is not None and r in bs.index), None)

    eps_values = []
    for col in ni_series.index:
        ni = _safe_float(ni_series[col])
        if ni is None:
            continue
        if sh_row is not None and bs is not None and col in bs.columns:
            shares = _safe_float(bs.loc[sh_row, col])
        else:
            shares = _safe_float(data.info.get("sharesOutstanding"))
        if shares and shares > 0 and ni is not None:
            eps_values.append(ni / shares)

    if len(eps_values) < 2:
        return None

    # Average EPS growth rate
    growth_rates = []
    for i in range(1, len(eps_values)):
        if eps_values[i] > 0 and eps_values[i - 1] > 0:
            g = (eps_values[i - 1] - eps_values[i]) / abs(eps_values[i]) * 100
            growth_rates.append(g)

    if not growth_rates:
        return None

    avg_growth = float(np.mean(growth_rates))
    if avg_growth <= 0:
        return None

    pe_data = calc_historical_pe(data)
    if pe_data is None:
        return None

    avg_peg = pe_data["avg_pe"] / avg_growth

    return {
        "avg_peg": avg_peg,
        "current_peg": current_peg,
        "years_available": pe_data["years_available"],
        "current_below_avg": current_peg < avg_peg,
    }


# ── Debt / EBITDA ─────────────────────────────────────────────────────────────

def calc_debt_to_ebitda(data: CompanyData) -> Optional[float]:
    """Returns total_debt / EBITDA. Negative EBITDA returns a large positive number (fails)."""
    total_debt = _safe_float(data.info.get("totalDebt"))
    ebitda = _safe_float(data.info.get("ebitda"))

    if total_debt is None or ebitda is None:
        return None

    if ebitda <= 0:
        return 999.0  # Signals automatic fail

    return total_debt / ebitda


# ── Revenue growth ────────────────────────────────────────────────────────────

def calc_revenue_growth(data: CompanyData) -> Optional[float]:
    """Returns YoY revenue growth as a percentage. None if unavailable."""
    # Try info first (most reliable for trailing 12m)
    growth = _safe_float(data.info.get("revenueGrowth"))
    if growth is not None:
        return growth * 100.0

    # Fallback: calculate from income statement
    income = data.income_stmt
    if income is None:
        return None

    rev_rows = ["Total Revenue", "Revenue"]
    rev_row = next((r for r in rev_rows if r in income.index), None)
    if rev_row is None:
        return None

    rev_series = income.loc[rev_row].dropna()
    if len(rev_series) < 2:
        return None

    latest = _safe_float(rev_series.iloc[0])
    prior = _safe_float(rev_series.iloc[1])

    if latest is None or prior is None or prior == 0:
        return None

    return (latest - prior) / prior * 100.0
