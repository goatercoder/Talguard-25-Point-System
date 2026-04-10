"""
Evaluates all 23 criteria against CompanyData + AI results + manual answers.
Returns a ScreenerResult with one CriterionResult per criterion.
"""

from datetime import datetime
from typing import Optional

from config import CRITERIA_CONFIG, FINANCIAL_SECTORS
from core.models import (
    CompanyData,
    CriterionResult,
    ScreenerResult,
    STATUS_PASS,
    STATUS_FAIL,
    STATUS_INSUFFICIENT_DATA,
    STATUS_NO_AI,
    STATUS_PENDING_MANUAL,
)
from core import calculators as calc


def _safe_float(val) -> Optional[float]:
    import numpy as np
    try:
        f = float(val)
        return None if (np.isnan(f) or np.isinf(f)) else f
    except Exception:
        return None


def _make(cid: int, status: str, actual=None, display: Optional[str] = None,
          source: Optional[str] = None, ai_reasoning: Optional[str] = None,
          ai_confidence: Optional[str] = None, ai_score: Optional[int] = None,
          error: Optional[str] = None) -> CriterionResult:
    cfg = CRITERIA_CONFIG[cid]
    points = 1 if status == STATUS_PASS else 0
    return CriterionResult(
        criterion_id=cid,
        name=cfg["name"],
        status=status,
        actual_value=actual,
        actual_display=display,
        threshold_display=cfg["threshold_display"],
        data_source=source,
        ai_reasoning=ai_reasoning,
        ai_confidence=ai_confidence,
        ai_score=ai_score,
        error_message=error,
        points=points,
    )


# ── Individual evaluators ────────────────────────────────────────────────────

def _eval_1(data: CompanyData, ai: dict) -> CriterionResult:
    """Durable Competitive Advantage (AI score ≥ 7)"""
    r = ai.get(1)
    if r is None:
        return _make(1, STATUS_NO_AI, error="OpenAI API not configured.")
    score = r.get("score")
    if score is None:
        return _make(1, STATUS_INSUFFICIENT_DATA, error="AI did not return a score.")
    passed = int(score) >= 7
    moat = r.get("moat_type", "")
    display = f"Score {score}/10 — {moat}" if moat else f"Score {score}/10"
    return _make(1, STATUS_PASS if passed else STATUS_FAIL,
                 actual=score, display=display,
                 ai_reasoning=r.get("reasoning"), ai_confidence=r.get("confidence"),
                 ai_score=int(score))


def _eval_2(data: CompanyData, _ai: dict) -> CriterionResult:
    """Dividend Consistency + Growth"""
    result = calc.calc_dividend_consistency(data)
    if result["no_dividends"]:
        return _make(2, STATUS_FAIL, display="No dividends paid", source="yfinance:dividends")
    if result["years_checked"] < 2:
        return _make(2, STATUS_INSUFFICIENT_DATA, error="Fewer than 2 years of dividend data.",
                     source="yfinance:dividends")
    status = STATUS_PASS if result["consistent"] else STATUS_FAIL
    cuts = "" if result.get("no_cuts", True) else " | Cuts detected"
    gaps = "" if result.get("no_gaps", True) else " | Gap years detected"
    display = f"{result['years_checked']} years consistent{cuts}{gaps}"
    return _make(2, status, display=display, source="yfinance:dividends")


def _eval_3(data: CompanyData, _ai: dict) -> CriterionResult:
    """Dividend Growth Rate ≥ 10%"""
    result = calc.calc_dividend_consistency(data)
    if result["no_dividends"]:
        return _make(3, STATUS_FAIL, display="No dividends paid", source="yfinance:dividends")
    growth = calc.calc_dividend_growth_rate(data)
    if growth is None:
        return _make(3, STATUS_INSUFFICIENT_DATA, error="Insufficient dividend history.",
                     source="yfinance:dividends")
    status = STATUS_PASS if growth >= 10.0 else STATUS_FAIL
    return _make(3, status, actual=growth, display=f"{growth:+.1f}% YoY", source="yfinance:dividends")


def _eval_4(data: CompanyData, _ai: dict) -> CriterionResult:
    """Share Buybacks ≥ 1%"""
    pct = calc.calc_buyback_pct(data)
    if pct is None:
        return _make(4, STATUS_INSUFFICIENT_DATA, error="Shares outstanding data unavailable.",
                     source="yfinance:balance_sheet")
    status = STATUS_PASS if pct >= 1.0 else STATUS_FAIL
    direction = "buyback" if pct > 0 else "dilution"
    display = f"{abs(pct):.1f}% share {direction} YoY"
    return _make(4, status, actual=pct, display=display, source="yfinance:balance_sheet")


def _eval_5(data: CompanyData, _ai: dict) -> CriterionResult:
    """Gross Margin ≥ 10%"""
    gm = _safe_float(data.info.get("grossMargins"))
    if gm is None:
        return _make(5, STATUS_INSUFFICIENT_DATA, error="Gross margin data unavailable.",
                     source="yfinance:info.grossMargins")
    gm_pct = gm * 100.0
    status = STATUS_PASS if gm_pct >= 10.0 else STATUS_FAIL
    return _make(5, status, actual=gm_pct, display=f"{gm_pct:.1f}%", source="yfinance:info.grossMargins")


def _eval_6(data: CompanyData, _ai: dict) -> CriterionResult:
    """Consistent Positive FCF (≥ 3 of last 4 years)"""
    fcf_list = calc.calc_fcf_history(data)
    if fcf_list is None:
        return _make(6, STATUS_INSUFFICIENT_DATA, error="Cash flow data unavailable.",
                     source="yfinance:cash_flow")
    valid = [v for v in fcf_list if v is not None]
    if len(valid) < 2:
        return _make(6, STATUS_INSUFFICIENT_DATA, error="Fewer than 2 years of FCF data.",
                     source="yfinance:cash_flow")
    positive_years = sum(1 for v in valid if v > 0)
    total_years = len(valid)
    status = STATUS_PASS if positive_years >= 3 else STATUS_FAIL
    display = f"{positive_years}/{total_years} years positive FCF"
    return _make(6, status, actual=positive_years, display=display, source="yfinance:cash_flow")


def _eval_7(data: CompanyData, _ai: dict) -> CriterionResult:
    """Operating Margin ≥ 15%"""
    om = _safe_float(data.info.get("operatingMargins"))
    if om is None:
        return _make(7, STATUS_INSUFFICIENT_DATA, error="Operating margin data unavailable.",
                     source="yfinance:info.operatingMargins")
    om_pct = om * 100.0
    status = STATUS_PASS if om_pct >= 15.0 else STATUS_FAIL
    return _make(7, status, actual=om_pct, display=f"{om_pct:.1f}%", source="yfinance:info.operatingMargins")


def _eval_8(data: CompanyData, _ai: dict) -> CriterionResult:
    """Debt / Equity ≤ 5.0x"""
    de = _safe_float(data.info.get("debtToEquity"))
    if de is None:
        return _make(8, STATUS_INSUFFICIENT_DATA, error="Debt/Equity data unavailable.",
                     source="yfinance:info.debtToEquity")
    # yfinance reports as a percentage (150 = 1.50x), divide by 100
    de_ratio = de / 100.0
    status = STATUS_PASS if de_ratio <= 5.0 else STATUS_FAIL
    return _make(8, status, actual=de_ratio, display=f"{de_ratio:.2f}x", source="yfinance:info.debtToEquity")


def _eval_9(data: CompanyData, _ai: dict) -> CriterionResult:
    """Market Cap / EBITDA (EV/EBITDA) < 10"""
    ev_ebitda = _safe_float(data.info.get("enterpriseToEbitda"))
    if ev_ebitda is None:
        return _make(9, STATUS_INSUFFICIENT_DATA, error="EV/EBITDA data unavailable.",
                     source="yfinance:info.enterpriseToEbitda")
    if ev_ebitda < 0:
        return _make(9, STATUS_FAIL, actual=ev_ebitda, display=f"{ev_ebitda:.1f}x (negative EBITDA)",
                     source="yfinance:info.enterpriseToEbitda")
    status = STATUS_PASS if ev_ebitda < 10.0 else STATUS_FAIL
    return _make(9, status, actual=ev_ebitda, display=f"{ev_ebitda:.1f}x", source="yfinance:info.enterpriseToEbitda")


def _eval_10(data: CompanyData, _ai: dict) -> CriterionResult:
    """P/E Below Historical Average"""
    result = calc.calc_historical_pe(data)
    if result is None:
        return _make(10, STATUS_INSUFFICIENT_DATA, error="Insufficient data for historical P/E calculation.",
                     source="yfinance:income_stmt+history")
    status = STATUS_PASS if result["current_below_avg"] else STATUS_FAIL
    caveat = f" ({result['years_available']}yr avg)" if result["years_available"] < 10 else ""
    display = f"Current {result['current_pe']:.1f}x vs avg {result['avg_pe']:.1f}x{caveat}"
    return _make(10, status, actual=result["current_pe"], display=display,
                 source="yfinance:income_stmt+history")


def _eval_11(data: CompanyData, _ai: dict) -> CriterionResult:
    """PEG Below Historical Average"""
    result = calc.calc_historical_peg(data)
    if result is None:
        return _make(11, STATUS_INSUFFICIENT_DATA, error="Insufficient data for historical PEG calculation.",
                     source="yfinance:income_stmt+info.pegRatio")
    status = STATUS_PASS if result["current_below_avg"] else STATUS_FAIL
    caveat = f" ({result['years_available']}yr avg)" if result["years_available"] < 10 else ""
    display = f"Current {result['current_peg']:.2f} vs avg {result['avg_peg']:.2f}{caveat}"
    return _make(11, status, actual=result["current_peg"], display=display,
                 source="yfinance:income_stmt+info.pegRatio")


def _eval_ai_binary(cid: int, ai: dict) -> CriterionResult:
    """Generic evaluator for binary AI criteria (#12, #13, #15, #20)."""
    r = ai.get(cid)
    if r is None:
        return _make(cid, STATUS_NO_AI, error="OpenAI API not configured.")
    result_val = r.get("result")
    if result_val is None:
        return _make(cid, STATUS_INSUFFICIENT_DATA, error="AI returned no result.",
                     ai_reasoning=r.get("reasoning"))
    status = STATUS_PASS if bool(result_val) else STATUS_FAIL
    display = "Pass" if bool(result_val) else "Fail"
    return _make(cid, status, display=display,
                 ai_reasoning=r.get("reasoning"), ai_confidence=r.get("confidence"))


def _eval_14(data: CompanyData, _ai: dict) -> CriterionResult:
    """ROE > 15% (ROA > 1% for financial sector)"""
    is_financial = data.sector in FINANCIAL_SECTORS

    if is_financial:
        roa = _safe_float(data.info.get("returnOnAssets"))
        if roa is None:
            return _make(14, STATUS_INSUFFICIENT_DATA, error="ROA data unavailable (financial sector).",
                         source="yfinance:info.returnOnAssets")
        roa_pct = roa * 100.0
        status = STATUS_PASS if roa_pct > 1.0 else STATUS_FAIL
        return _make(14, status, actual=roa_pct, display=f"ROA {roa_pct:.1f}% (financial sector)",
                     source="yfinance:info.returnOnAssets")
    else:
        roe = _safe_float(data.info.get("returnOnEquity"))
        if roe is None:
            return _make(14, STATUS_INSUFFICIENT_DATA, error="ROE data unavailable.",
                         source="yfinance:info.returnOnEquity")
        roe_pct = roe * 100.0
        status = STATUS_PASS if roe_pct > 15.0 else STATUS_FAIL
        return _make(14, status, actual=roe_pct, display=f"ROE {roe_pct:.1f}%",
                     source="yfinance:info.returnOnEquity")


def _eval_16(data: CompanyData, _ai: dict) -> CriterionResult:
    """Fast Sales Growth ≥ 10% YoY"""
    growth = calc.calc_revenue_growth(data)
    if growth is None:
        return _make(16, STATUS_INSUFFICIENT_DATA, error="Revenue growth data unavailable.",
                     source="yfinance:income_stmt")
    status = STATUS_PASS if growth >= 10.0 else STATUS_FAIL
    return _make(16, status, actual=growth, display=f"{growth:+.1f}% YoY", source="yfinance:income_stmt")


def _eval_17(data: CompanyData, _ai: dict) -> CriterionResult:
    """Current Ratio > 1.0x"""
    cr = _safe_float(data.info.get("currentRatio"))
    if cr is None:
        return _make(17, STATUS_INSUFFICIENT_DATA, error="Current ratio data unavailable.",
                     source="yfinance:info.currentRatio")
    status = STATUS_PASS if cr > 1.0 else STATUS_FAIL
    return _make(17, status, actual=cr, display=f"{cr:.2f}x", source="yfinance:info.currentRatio")


def _eval_18(data: CompanyData, _ai: dict) -> CriterionResult:
    """Share Buybacks (confirmed — any positive buyback)"""
    pct = calc.calc_buyback_pct(data)
    if pct is None:
        return _make(18, STATUS_INSUFFICIENT_DATA, error="Shares outstanding data unavailable.",
                     source="yfinance:balance_sheet")
    status = STATUS_PASS if pct > 0 else STATUS_FAIL
    direction = "buyback" if pct > 0 else "dilution"
    display = f"{abs(pct):.1f}% share {direction} YoY"
    return _make(18, status, actual=pct, display=display, source="yfinance:balance_sheet")


def _eval_19(data: CompanyData, _ai: dict) -> CriterionResult:
    """Debt / EBITDA < 6.0x"""
    ratio = calc.calc_debt_to_ebitda(data)
    if ratio is None:
        return _make(19, STATUS_INSUFFICIENT_DATA, error="Total debt or EBITDA data unavailable.",
                     source="yfinance:info.totalDebt+ebitda")
    if ratio == 999.0:
        return _make(19, STATUS_FAIL, display="Negative EBITDA", source="yfinance:info.ebitda")
    status = STATUS_PASS if ratio < 6.0 else STATUS_FAIL
    return _make(19, status, actual=ratio, display=f"{ratio:.2f}x", source="yfinance:info.totalDebt+ebitda")


def _eval_21_pending() -> CriterionResult:
    """Criterion 21 awaiting analyst manual input."""
    cfg = CRITERIA_CONFIG[21]
    return CriterionResult(
        criterion_id=21,
        name=cfg["name"],
        status=STATUS_PENDING_MANUAL,
        threshold_display=cfg["threshold_display"],
        points=0,
    )


def _eval_21_answered(answer: bool) -> CriterionResult:
    status = STATUS_PASS if answer else STATUS_FAIL
    return _make(21, status, display="Yes — analyst understands business" if answer else "No — needs more research")


def _eval_22(data: CompanyData, _ai: dict) -> CriterionResult:
    """Forward P/E < 25x"""
    fpe = _safe_float(data.info.get("forwardPE"))
    if fpe is None:
        return _make(22, STATUS_INSUFFICIENT_DATA, error="Forward P/E data unavailable.",
                     source="yfinance:info.forwardPE")
    status = STATUS_PASS if fpe < 25.0 else STATUS_FAIL
    return _make(22, status, actual=fpe, display=f"{fpe:.1f}x", source="yfinance:info.forwardPE")


def _eval_23(data: CompanyData, _ai: dict) -> CriterionResult:
    """PEG Ratio ≤ 2.0"""
    from core.calculators import get_current_peg
    peg = get_current_peg(data.info)
    if peg is None:
        return _make(23, STATUS_INSUFFICIENT_DATA,
                     error="PEG ratio unavailable (tried pegRatio, trailingPegRatio, and PE/growth calculation).",
                     source="yfinance:info.pegRatio/trailingPegRatio")
    # Label the source field used
    if data.info.get("pegRatio"):
        src = "yfinance:info.pegRatio"
    elif data.info.get("trailingPegRatio"):
        src = "yfinance:info.trailingPegRatio"
    else:
        src = "yfinance:calculated (trailingPE/earningsGrowth)"
    status = STATUS_PASS if peg <= 2.0 else STATUS_FAIL
    return _make(23, status, actual=peg, display=f"{peg:.2f}", source=src)


# ── Main evaluator ────────────────────────────────────────────────────────────

_EVALUATORS = {
    1: _eval_1,
    2: _eval_2,
    3: _eval_3,
    4: _eval_4,
    5: _eval_5,
    6: _eval_6,
    7: _eval_7,
    8: _eval_8,
    9: _eval_9,
    10: _eval_10,
    11: _eval_11,
    12: lambda d, ai: _eval_ai_binary(12, ai),
    13: lambda d, ai: _eval_ai_binary(13, ai),
    14: _eval_14,
    15: lambda d, ai: _eval_ai_binary(15, ai),
    16: _eval_16,
    17: _eval_17,
    18: _eval_18,
    19: _eval_19,
    20: lambda d, ai: _eval_ai_binary(20, ai),
    22: _eval_22,
    23: _eval_23,
}


def evaluate_all(
    data: CompanyData,
    ai_results: dict,
    manual_answer_21: Optional[bool] = None,
) -> ScreenerResult:
    """
    Evaluate all 23 criteria.

    Args:
        data: Fetched company data.
        ai_results: Dict mapping criterion_id → AI response dict.
                    Pass empty dict {} if AI is not configured.
        manual_answer_21: True/False once analyst answers criterion 21,
                          None = criterion still pending.

    Returns ScreenerResult with all 23 CriterionResult entries.
    """
    criteria: list[CriterionResult] = []

    for cid in range(1, 24):
        if cid == 21:
            if manual_answer_21 is None:
                criteria.append(_eval_21_pending())
            else:
                criteria.append(_eval_21_answered(manual_answer_21))
            continue

        evaluator = _EVALUATORS.get(cid)
        if evaluator is None:
            continue

        criteria.append(evaluator(data, ai_results))

    market_cap = _safe_float(data.info.get("marketCap"))

    return ScreenerResult(
        ticker=data.ticker_symbol,
        company_name=data.company_name,
        sector=data.sector,
        industry=data.industry,
        market_cap=market_cap,
        analysis_date=datetime.now(),
        criteria=criteria,
        manual_pending=(manual_answer_21 is None),
    )
