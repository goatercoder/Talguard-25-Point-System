"""
Data models for the screener. All other modules work against these contracts.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import pandas as pd


# ── Status constants ────────────────────────────────────────────────────────

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
STATUS_NO_AI = "NO_AI_CONFIGURED"
STATUS_PENDING_MANUAL = "PENDING_MANUAL"


# ── Raw company data (fetched once, shared everywhere) ──────────────────────

@dataclass
class CompanyData:
    ticker_symbol: str
    info: dict = field(default_factory=dict)
    income_stmt: Optional[pd.DataFrame] = None    # Annual, up to 4 years
    balance_sheet: Optional[pd.DataFrame] = None  # Annual, up to 4 years
    cash_flow: Optional[pd.DataFrame] = None      # Annual, up to 4 years
    dividends: Optional[pd.Series] = None         # Full history
    price_history: Optional[pd.DataFrame] = None  # 10-year daily OHLCV
    insider_transactions: Optional[pd.DataFrame] = None
    fetch_errors: dict = field(default_factory=dict)  # field_name → error message
    fetch_timestamp: Optional[datetime] = None

    @property
    def company_name(self) -> str:
        return self.info.get("longName") or self.info.get("shortName") or self.ticker_symbol

    @property
    def sector(self) -> str:
        return self.info.get("sector", "Unknown")

    @property
    def industry(self) -> str:
        return self.info.get("industry", "Unknown")

    @property
    def business_summary(self) -> str:
        return self.info.get("longBusinessSummary", "No description available.")

    @property
    def is_valid(self) -> bool:
        """True if info was fetched and contains a valid symbol."""
        return bool(self.info.get("symbol") or self.info.get("regularMarketPrice"))


# ── Per-criterion result ────────────────────────────────────────────────────

@dataclass
class CriterionResult:
    criterion_id: int
    name: str
    status: str                            # One of the STATUS_* constants
    actual_value: Optional[object] = None  # The raw metric (float, str, etc.)
    actual_display: Optional[str] = None   # Human-readable version, e.g. "29.8%"
    threshold_display: Optional[str] = None
    data_source: Optional[str] = None      # e.g. "yfinance:info.operatingMargins"
    ai_reasoning: Optional[str] = None
    ai_confidence: Optional[str] = None    # "low" | "medium" | "high"
    ai_score: Optional[int] = None         # Only for criterion #1
    error_message: Optional[str] = None
    points: int = 0                        # 0 or 1


# ── Full screener result ────────────────────────────────────────────────────

@dataclass
class ScreenerResult:
    ticker: str
    company_name: str
    sector: str
    industry: str
    market_cap: Optional[float]
    analysis_date: datetime
    criteria: list[CriterionResult] = field(default_factory=list)
    manual_pending: bool = False           # True until criterion 21 is answered

    @property
    def total_points(self) -> int:
        return sum(c.points for c in self.criteria)

    @property
    def max_points(self) -> int:
        """Excludes PENDING_MANUAL criteria from denominator until answered."""
        return sum(
            1 for c in self.criteria
            if c.status != STATUS_PENDING_MANUAL
        )

    @property
    def passed(self) -> bool:
        from config import PASSING_SCORE
        return self.total_points >= PASSING_SCORE

    @property
    def core_criteria(self) -> list[CriterionResult]:
        from config import GROUP_CORE
        ids = {i for i, v in __import__("config").CRITERIA_CONFIG.items() if v["group"] == GROUP_CORE}
        return [c for c in self.criteria if c.criterion_id in ids]

    @property
    def additional_criteria(self) -> list[CriterionResult]:
        from config import GROUP_ADDITIONAL
        ids = {i for i, v in __import__("config").CRITERIA_CONFIG.items() if v["group"] == GROUP_ADDITIONAL}
        return [c for c in self.criteria if c.criterion_id in ids]

    @property
    def valuation_criteria(self) -> list[CriterionResult]:
        from config import GROUP_VALUATION
        ids = {i for i, v in __import__("config").CRITERIA_CONFIG.items() if v["group"] == GROUP_VALUATION}
        return [c for c in self.criteria if c.criterion_id in ids]

    def to_dict(self) -> dict:
        """Serializable representation for history / export."""
        return {
            "ticker": self.ticker,
            "company_name": self.company_name,
            "sector": self.sector,
            "industry": self.industry,
            "market_cap": self.market_cap,
            "analysis_date": self.analysis_date.isoformat(),
            "total_points": self.total_points,
            "passed": self.passed,
            "criteria": [
                {
                    "id": c.criterion_id,
                    "name": c.name,
                    "status": c.status,
                    "actual_display": c.actual_display,
                    "threshold_display": c.threshold_display,
                    "points": c.points,
                    "ai_reasoning": c.ai_reasoning,
                    "error_message": c.error_message,
                }
                for c in self.criteria
            ],
        }
