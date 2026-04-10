"""
Central configuration: all criterion thresholds, metadata, and scoring constants.
Changing a threshold means editing exactly this file.
"""

PASSING_SCORE = 16
TOTAL_CRITERIA = 23

# Criterion types
TYPE_QUANT = "quant"       # Auto-evaluated from yfinance data
TYPE_AI = "ai"             # Evaluated via OpenAI with web search
TYPE_MANUAL = "manual"     # Analyst answers yes/no

# Groups
GROUP_CORE = "core"
GROUP_ADDITIONAL = "additional"
GROUP_VALUATION = "valuation"

# Moat types used in criterion #1 AI prompt
MOAT_TYPES = [
    "Strong Brand",
    "Monopoly",
    "Oligopoly",
    "Consumer Monopoly",
    "Toll Bridge",
    "Network Effects",
    "Switching Costs",
    "Cost Advantages",
    "Other",
]

CRITERIA_CONFIG: dict[int, dict] = {
    1: {
        "name": "Durable Competitive Advantage",
        "description": "AI scores moat strength 1–10; needs ≥7 to pass",
        "type": TYPE_AI,
        "threshold": 7,
        "threshold_display": "Score ≥ 7/10",
        "group": GROUP_CORE,
    },
    2: {
        "name": "Dividend Consistency + Growth",
        "description": "Company has paid dividends consistently with no cuts in 5+ years",
        "type": TYPE_QUANT,
        "threshold": None,
        "threshold_display": "No dividend cuts (5yr)",
        "group": GROUP_CORE,
    },
    3: {
        "name": "Dividend Growth Rate ≥ 10%",
        "description": "Most recent annual dividend growth ≥ 10% YoY",
        "type": TYPE_QUANT,
        "threshold": 10.0,
        "threshold_display": "≥ 10% YoY",
        "group": GROUP_CORE,
    },
    4: {
        "name": "Share Buybacks ≥ 1%",
        "description": "Shares outstanding reduced by ≥ 1% YoY",
        "type": TYPE_QUANT,
        "threshold": 1.0,
        "threshold_display": "≥ 1% share reduction YoY",
        "group": GROUP_CORE,
    },
    5: {
        "name": "Gross Margin ≥ 10%",
        "description": "Trailing gross margin ≥ 10%",
        "type": TYPE_QUANT,
        "threshold": 10.0,
        "threshold_display": "≥ 10%",
        "group": GROUP_CORE,
    },
    6: {
        "name": "Consistent Positive Free Cash Flow",
        "description": "Positive FCF in at least 3 of the last 4 fiscal years",
        "type": TYPE_QUANT,
        "threshold": 3,
        "threshold_display": "≥ 3 of last 4 years positive",
        "group": GROUP_CORE,
    },
    7: {
        "name": "Operating Margin ≥ 15%",
        "description": "Trailing operating margin ≥ 15%",
        "type": TYPE_QUANT,
        "threshold": 15.0,
        "threshold_display": "≥ 15%",
        "group": GROUP_CORE,
    },
    8: {
        "name": "Debt / Equity ≤ 5.0x",
        "description": "Total debt to equity ratio ≤ 5.0x",
        "type": TYPE_QUANT,
        "threshold": 5.0,
        "threshold_display": "≤ 5.0x",
        "group": GROUP_CORE,
    },
    9: {
        "name": "Market Cap / EBITDA < 10",
        "description": "Enterprise Value / EBITDA multiple < 10",
        "type": TYPE_QUANT,
        "threshold": 10.0,
        "threshold_display": "< 10x",
        "group": GROUP_CORE,
    },
    10: {
        "name": "P/E Below Historical Average",
        "description": "Current trailing P/E is below the 4-year historical average P/E",
        "type": TYPE_QUANT,
        "threshold": None,
        "threshold_display": "Current < 4yr avg",
        "group": GROUP_CORE,
    },
    11: {
        "name": "PEG Below Historical Average",
        "description": "Current PEG ratio is below the 4-year historical average PEG",
        "type": TYPE_QUANT,
        "threshold": None,
        "threshold_display": "Current < 4yr avg",
        "group": GROUP_CORE,
    },
    12: {
        "name": "Business Exists in 100 Years",
        "description": "AI assesses whether this business model is likely to remain viable in 100 years",
        "type": TYPE_AI,
        "threshold": None,
        "threshold_display": "Pass",
        "group": GROUP_CORE,
    },
    13: {
        "name": "#1 by Revenue in Niche",
        "description": "AI assesses whether this company is the revenue leader in its specific niche",
        "type": TYPE_AI,
        "threshold": None,
        "threshold_display": "Pass",
        "group": GROUP_CORE,
    },
    14: {
        "name": "ROE > 15% (ROA > 1% for financials)",
        "description": "Return on equity > 15%; for financial sector companies, ROA > 1% is used instead",
        "type": TYPE_QUANT,
        "threshold": 15.0,
        "threshold_display": "ROE > 15% (or ROA > 1%)",
        "group": GROUP_CORE,
    },
    15: {
        "name": "Future Products / Pipeline",
        "description": "AI assesses whether the company has promising products or projects in development",
        "type": TYPE_AI,
        "threshold": None,
        "threshold_display": "Pass",
        "group": GROUP_ADDITIONAL,
    },
    16: {
        "name": "Fast Sales Growth ≥ 10% YoY",
        "description": "Most recent annual revenue growth ≥ 10% YoY",
        "type": TYPE_QUANT,
        "threshold": 10.0,
        "threshold_display": "≥ 10% YoY",
        "group": GROUP_ADDITIONAL,
    },
    17: {
        "name": "Current Ratio > 1.0x",
        "description": "Current assets / current liabilities > 1.0x",
        "type": TYPE_QUANT,
        "threshold": 1.0,
        "threshold_display": "> 1.0x",
        "group": GROUP_ADDITIONAL,
    },
    18: {
        "name": "Share Buybacks (confirmed)",
        "description": "Confirmation that the company is actively repurchasing shares",
        "type": TYPE_QUANT,
        "threshold": 0.0,
        "threshold_display": "Any positive buyback",
        "group": GROUP_ADDITIONAL,
    },
    19: {
        "name": "Debt / EBITDA < 6.0x",
        "description": "Total debt divided by EBITDA < 6.0x",
        "type": TYPE_QUANT,
        "threshold": 6.0,
        "threshold_display": "< 6.0x",
        "group": GROUP_ADDITIONAL,
    },
    20: {
        "name": "Management Goodwill / Integrity",
        "description": "AI assesses management track record, insider behavior, and governance quality",
        "type": TYPE_AI,
        "threshold": None,
        "threshold_display": "Pass",
        "group": GROUP_ADDITIONAL,
    },
    21: {
        "name": "Do You Understand the Company?",
        "description": "Analyst confirms they sufficiently understand the business model and competitive dynamics",
        "type": TYPE_MANUAL,
        "threshold": None,
        "threshold_display": "Analyst: Yes",
        "group": GROUP_ADDITIONAL,
    },
    22: {
        "name": "Forward P/E < 25x",
        "description": "Forward price-to-earnings ratio < 25x",
        "type": TYPE_QUANT,
        "threshold": 25.0,
        "threshold_display": "< 25x",
        "group": GROUP_VALUATION,
    },
    23: {
        "name": "PEG Ratio ≤ 2.0",
        "description": "Price/Earnings to Growth ratio ≤ 2.0",
        "type": TYPE_QUANT,
        "threshold": 2.0,
        "threshold_display": "≤ 2.0",
        "group": GROUP_VALUATION,
    },
}

# Financial sector detection
FINANCIAL_SECTORS = {"Financial Services", "Finance", "Banking", "Insurance"}

# Settings file location (user home, not project dir — never accidentally committed)
import os
SETTINGS_PATH = os.path.join(os.path.expanduser("~"), ".talguard", "settings.json")
HISTORY_PATH = os.path.join(os.path.dirname(__file__), "results", "history.json")

# OpenAI model options
AI_MODELS = {
    "gpt-4o-mini": "GPT-4o Mini (fast, cheap — recommended)",
    "gpt-4o": "GPT-4o (most accurate, higher cost)",
}
DEFAULT_AI_MODEL = "gpt-4o-mini"
