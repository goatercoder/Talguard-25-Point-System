"""
Prompt templates for the 5 qualitative criteria evaluated via OpenAI.
All prompts request JSON output for reliable parsing.
"""

from config import MOAT_TYPES
from core.models import CompanyData


def _fmt_market_cap(mc) -> str:
    if mc is None:
        return "N/A"
    if mc >= 1e12:
        return f"${mc/1e12:.1f}T"
    if mc >= 1e9:
        return f"${mc/1e9:.1f}B"
    if mc >= 1e6:
        return f"${mc/1e6:.1f}M"
    return f"${mc:,.0f}"


def _fmt_pct(val) -> str:
    if val is None:
        return "N/A"
    try:
        return f"{float(val)*100:.1f}%"
    except Exception:
        return "N/A"


def _fmt_insider_tx(df) -> str:
    if df is None or len(df) == 0:
        return "No recent insider transactions available."
    try:
        rows = []
        for _, row in df.head(10).iterrows():
            name = row.get("Insider Trading", row.get("Name", "Unknown"))
            tx_type = row.get("Transaction", row.get("Type", "Unknown"))
            shares = row.get("Shares", "N/A")
            value = row.get("Value", "N/A")
            rows.append(f"  - {name}: {tx_type}, {shares} shares, ${value}")
        return "\n".join(rows)
    except Exception:
        return "Insider transaction data format unrecognized."


# ── System message (shared) ──────────────────────────────────────────────────

SYSTEM_MESSAGE = (
    "You are a senior equity research analyst specializing in long-term quality investing. "
    "You conduct thorough due diligence on publicly listed companies. "
    "Use your knowledge and any available web search tools to research the company before answering. "
    "Respond ONLY with valid JSON matching the schema requested — no markdown, no commentary outside JSON."
)


# ── Criterion 1: Durable Competitive Advantage ───────────────────────────────

def prompt_moat(data: CompanyData) -> str:
    moat_types_str = "\n".join(f"  - {m}" for m in MOAT_TYPES)
    return f"""Analyze the durable competitive advantage (economic moat) of {data.company_name}.

Company Profile:
- Ticker: {data.ticker_symbol}
- Sector: {data.sector}
- Industry: {data.industry}
- Market Cap: {_fmt_market_cap(data.info.get('marketCap'))}
- Gross Margin: {_fmt_pct(data.info.get('grossMargins'))}
- Operating Margin: {_fmt_pct(data.info.get('operatingMargins'))}
- ROE: {_fmt_pct(data.info.get('returnOnEquity'))}
- Business Description: {data.business_summary[:600]}

Please use web search to verify current competitive positioning, market share, and any recent competitive threats.

Score the company's durable competitive advantage on a scale of 1 to 10:
  1–3: No meaningful moat (commodity business, highly competitive, easy to replicate)
  4–6: Narrow moat (some advantage but not durable long-term)
  7–8: Wide moat (strong brand, network effects, switching costs, or regulatory advantages)
  9–10: Exceptional moat (near-monopoly, irreplaceable infrastructure, or dominant platform)

Moat types to consider:
{moat_types_str}

Respond with this exact JSON:
{{
  "score": <integer 1-10>,
  "moat_type": "<primary moat type from list above>",
  "reasoning": "<2–3 sentences explaining the score>",
  "confidence": "<low|medium|high>"
}}"""


# ── Criterion 12: Business Exists in 100 Years ──────────────────────────────

def prompt_longevity(data: CompanyData) -> str:
    return f"""Assess whether {data.company_name} is likely to remain a viable, relevant business in 100 years.

Company Profile:
- Ticker: {data.ticker_symbol}
- Sector: {data.sector}
- Industry: {data.industry}
- Business Description: {data.business_summary[:600]}

Please use web search to research the company's current market position, any existential threats, and industry trajectory.

Consider:
- Is this industry likely to exist in 100 years?
- Is this specific company's business model resilient to technological disruption?
- Does the company have a track record of adapting to change?
- Are there regulatory, environmental, or societal forces that could eliminate this business?

Respond with this exact JSON:
{{
  "result": <true if likely to exist, false if unlikely>,
  "reasoning": "<2–3 sentences explaining your assessment>",
  "confidence": "<low|medium|high>",
  "caveats": "<any important qualifications or assumptions>"
}}"""


# ── Criterion 13: #1 by Revenue in Niche ─────────────────────────────────────

def prompt_market_leader(data: CompanyData) -> str:
    revenue = data.info.get("totalRevenue") or data.info.get("revenue")
    rev_str = _fmt_market_cap(revenue) if revenue else "N/A"
    return f"""Assess whether {data.company_name} is the #1 company by revenue in its specific market niche.

Company Profile:
- Ticker: {data.ticker_symbol}
- Sector: {data.sector}
- Industry: {data.industry}
- Annual Revenue: {rev_str}
- Business Description: {data.business_summary[:600]}

Please use web search to research the competitive landscape, current market share data, and revenue rankings in the relevant niche.

Consider:
- Is this company clearly the revenue leader in its primary market segment?
- Are there larger or faster-growing competitors?
- Is the niche specific enough for this company to be dominant?

Respond with this exact JSON:
{{
  "result": <true if #1 by revenue in niche, false otherwise>,
  "reasoning": "<2–3 sentences explaining your assessment, naming key competitors>",
  "confidence": "<low|medium|high>",
  "caveats": "<any important qualifications>"
}}"""


# ── Criterion 15: Future Products / Pipeline ─────────────────────────────────

def prompt_future_products(data: CompanyData) -> str:
    rd_expense = data.info.get("researchAndDevelopmentExpenses") or data.info.get("researchDevelopment")
    rd_str = _fmt_market_cap(rd_expense) if rd_expense else "N/A"
    return f"""Assess whether {data.company_name} has a promising pipeline of future products or projects in development.

Company Profile:
- Ticker: {data.ticker_symbol}
- Sector: {data.sector}
- Industry: {data.industry}
- R&D Spending: {rd_str}
- Business Description: {data.business_summary[:600]}

Please use web search to research recently announced products, pipeline projects, R&D initiatives, and management guidance on future growth areas.

Consider:
- Does the company have clear product/service pipelines or growth initiatives?
- Is there evidence of innovation investment (R&D, patents, acquisitions)?
- Are future products likely to be meaningful revenue contributors?
- Are they expanding into adjacent markets?

Respond with this exact JSON:
{{
  "result": <true if promising pipeline exists, false if pipeline is weak or absent>,
  "reasoning": "<2–3 sentences describing specific future products or initiatives>",
  "confidence": "<low|medium|high>",
  "caveats": "<any important qualifications>"
}}"""


# ── Criterion 20: Management Goodwill / Integrity ────────────────────────────

def prompt_management(data: CompanyData) -> str:
    ceo_name = "Unknown"
    officers = data.info.get("companyOfficers", [])
    if officers:
        ceo_name = officers[0].get("name", "Unknown")

    insider_tx_str = _fmt_insider_tx(data.insider_transactions)

    return f"""Assess the integrity and goodwill of {data.company_name}'s management team.

Company Profile:
- Ticker: {data.ticker_symbol}
- Sector: {data.sector}
- Industry: {data.industry}
- CEO: {ceo_name}

Recent Insider Transactions (last 12 months):
{insider_tx_str}

Please use web search to research the management team's track record, any governance controversies, shareholder-friendly actions, and alignment with long-term investor interests.

Consider:
- Do insiders buy shares with their own money (bullish signal of conviction)?
- Has management delivered on past strategic guidance?
- Are there known fraud, litigation, or ethics concerns?
- Does management communicate transparently with shareholders?
- Is compensation aligned with long-term performance?

Respond with this exact JSON:
{{
  "result": <true if management shows strong integrity and goodwill, false if concerns exist>,
  "reasoning": "<2–3 sentences explaining your assessment>",
  "confidence": "<low|medium|high>",
  "caveats": "<any important qualifications or known limitations>"
}}"""


# ── Dispatch table ─────────────────────────────────────────────────────────

PROMPT_BUILDERS = {
    1:  prompt_moat,
    12: prompt_longevity,
    13: prompt_market_leader,
    15: prompt_future_products,
    20: prompt_management,
}
