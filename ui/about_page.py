"""
About / Description page explaining the Talguard 23-point system.
"""

import streamlit as st
from config import CRITERIA_CONFIG, PASSING_SCORE, TOTAL_CRITERIA, MOAT_TYPES, GROUP_CORE, GROUP_ADDITIONAL, GROUP_VALUATION


def render_about():
    st.markdown(
        """
        <div style="max-width:860px">
          <div style="font-size:0.75em;letter-spacing:0.14em;text-transform:uppercase;
                      color:#475569;margin-bottom:8px">Methodology</div>
          <h1 style="font-size:2.2em;font-weight:800;color:#f1f5f9;margin:0 0 12px 0;line-height:1.1">
            The Talguard 23-Point<br>Quality Investment System
          </h1>
          <p style="color:#94a3b8;font-size:1.05em;line-height:1.7;margin-bottom:32px">
            A rigorous, systematic framework for identifying high-quality businesses at reasonable valuations.
            Each company is scored across 23 criteria spanning competitive positioning, financial strength,
            management quality, and valuation. A score of 16 or above signals a potential investment candidate.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Overview metrics ──────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    metric_style = """
        background:#111827;border:1px solid #1f2937;border-radius:10px;
        padding:18px 20px;text-align:center
    """
    with col1:
        st.markdown(
            f'<div style="{metric_style}">'
            f'<div style="font-size:2em;font-weight:800;color:#3b82f6">{TOTAL_CRITERIA}</div>'
            f'<div style="color:#94a3b8;font-size:0.85em;margin-top:4px">Total Criteria</div>'
            f'</div>', unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f'<div style="{metric_style}">'
            f'<div style="font-size:2em;font-weight:800;color:#10b981">{PASSING_SCORE}</div>'
            f'<div style="color:#94a3b8;font-size:0.85em;margin-top:4px">Points to Pass</div>'
            f'</div>', unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f'<div style="{metric_style}">'
            f'<div style="font-size:2em;font-weight:800;color:#6366f1">17</div>'
            f'<div style="color:#94a3b8;font-size:0.85em;margin-top:4px">Auto-Evaluated</div>'
            f'</div>', unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            f'<div style="{metric_style}">'
            f'<div style="font-size:2em;font-weight:800;color:#8b5cf6">5</div>'
            f'<div style="color:#94a3b8;font-size:0.85em;margin-top:4px">AI-Evaluated</div>'
            f'</div>', unsafe_allow_html=True
        )

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── Criteria sections ─────────────────────────────────────────────────────
    sections = [
        (GROUP_CORE,       "Core Checklist",       "The foundation — durable business quality, financial health, and return profile."),
        (GROUP_ADDITIONAL, "Additional Checklist",  "Growth trajectory, capital structure, and analyst conviction."),
        (GROUP_VALUATION,  "Valuation",             "Entry price discipline — ensuring you don't overpay for quality."),
    ]

    type_colors = {"quant": "#6366f1", "ai": "#8b5cf6", "manual": "#f59e0b"}
    type_labels = {"quant": "Quantitative", "ai": "AI · Web Search", "manual": "Manual"}

    for group_key, group_title, group_desc in sections:
        group_items = {cid: v for cid, v in CRITERIA_CONFIG.items() if v["group"] == group_key}
        count = len(group_items)

        st.markdown(
            f"""
            <div style="margin:32px 0 12px 0">
              <h2 style="font-size:1.2em;font-weight:700;color:#f1f5f9;margin:0 0 4px 0">
                {group_title}
                <span style="font-size:0.65em;color:#475569;font-weight:400;margin-left:8px">
                  {count} criteria
                </span>
              </h2>
              <p style="color:#64748b;font-size:0.9em;margin:0">{group_desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for cid, cfg in group_items.items():
            ctype = cfg["type"]
            tc = type_colors.get(ctype, "#6b7280")
            tl = type_labels.get(ctype, "")
            threshold = cfg["threshold_display"]

            st.markdown(
                f"""
                <div style="display:flex;gap:0;margin-bottom:6px;border-radius:8px;
                            overflow:hidden;border:1px solid #1f2937">
                  <div style="width:36px;background:#1f2937;display:flex;align-items:center;
                              justify-content:center;color:#475569;font-size:0.8em;font-weight:600;
                              flex-shrink:0">{cid}</div>
                  <div style="flex:1;background:#111827;padding:11px 16px">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;flex-wrap:wrap">
                      <div>
                        <span style="font-weight:600;color:#f1f5f9;font-size:0.95em">{cfg['name']}</span>
                        <span style="font-size:0.7em;color:{tc};background:{tc}18;
                                     padding:1px 7px;border-radius:20px;margin-left:8px">{tl}</span>
                        <div style="color:#64748b;font-size:0.83em;margin-top:3px">{cfg['description']}</div>
                      </div>
                      <div style="color:#94a3b8;font-size:0.8em;white-space:nowrap;
                                  background:#1f2937;padding:2px 10px;border-radius:6px;
                                  flex-shrink:0">{threshold}</div>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Moat types ────────────────────────────────────────────────────────────
    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <h2 style="font-size:1.2em;font-weight:700;color:#f1f5f9;margin:0 0 4px 0">
          Moat / Competitive Advantage Types
        </h2>
        <p style="color:#64748b;font-size:0.9em;margin:0 0 12px 0">
          For Criterion #1, the AI scores the company's moat strength 1–10 and identifies its primary source.
        </p>
        """,
        unsafe_allow_html=True,
    )

    moat_descriptions = {
        "Strong Brand":      "A brand commanding premium pricing and customer loyalty (e.g., Coca-Cola, Louis Vuitton).",
        "Monopoly":          "The sole provider in a market, often due to regulation or exclusive assets.",
        "Oligopoly":         "One of a few dominant players with high barriers to entry (e.g., credit card networks).",
        "Consumer Monopoly": "A product so embedded in daily life that switching feels impossible (e.g., iPhone ecosystem).",
        "Toll Bridge":       "Unavoidable intermediary that collects fees from all participants (e.g., payment rails, exchanges).",
        "Network Effects":   "The product becomes more valuable as more people use it (e.g., social platforms, marketplaces).",
        "Switching Costs":   "High cost or friction to replace the product/service (e.g., enterprise software, cloud infra).",
        "Cost Advantages":   "Structural ability to produce at lower cost than competitors (e.g., scale, geography, process).",
    }

    cols = st.columns(2)
    for i, (moat, desc) in enumerate(moat_descriptions.items()):
        with cols[i % 2]:
            st.markdown(
                f"""
                <div style="background:#111827;border:1px solid #1f2937;border-radius:8px;
                            padding:12px 16px;margin-bottom:8px">
                  <div style="font-weight:600;color:#f1f5f9;font-size:0.9em">{moat}</div>
                  <div style="color:#64748b;font-size:0.82em;margin-top:3px;line-height:1.5">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── How to use ────────────────────────────────────────────────────────────
    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <h2 style="font-size:1.2em;font-weight:700;color:#f1f5f9;margin:0 0 16px 0">
          How to Use This Tool
        </h2>
        """,
        unsafe_allow_html=True,
    )

    steps = [
        ("1", "Enter a Ticker", "Type any stock symbol in the sidebar (e.g. AAPL, KO, MSFT) and click Analyze."),
        ("2", "Review Quantitative Criteria", "17 criteria are auto-fetched from Yahoo Finance and evaluated immediately."),
        ("3", "Add Your OpenAI Key", "Go to Settings and enter your OpenAI API key to enable AI analysis of 5 qualitative criteria with live web search."),
        ("4", "Answer the Manual Criterion", "Criterion #21 asks whether you understand the company — your honest answer counts as one point."),
        ("5", "Interpret the Score", "16+ points = candidate worth deeper research. Below 16 = does not meet the quality threshold."),
        ("6", "Track Your Watchlist", "Use the Portfolio page to track multiple tickers and compare scores side-by-side."),
    ]

    for num, title, desc in steps:
        st.markdown(
            f"""
            <div style="display:flex;gap:16px;margin-bottom:12px;align-items:flex-start">
              <div style="width:32px;height:32px;background:#3b82f620;color:#3b82f6;
                          border-radius:50%;display:flex;align-items:center;justify-content:center;
                          font-weight:700;font-size:0.9em;flex-shrink:0">{num}</div>
              <div>
                <div style="font-weight:600;color:#f1f5f9;font-size:0.95em">{title}</div>
                <div style="color:#64748b;font-size:0.85em;margin-top:2px;line-height:1.5">{desc}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Data sources ──────────────────────────────────────────────────────────
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="background:#111827;border:1px solid #1f2937;border-radius:10px;padding:20px 24px">
          <div style="font-weight:700;color:#f1f5f9;margin-bottom:12px">Data Sources & Limitations</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
            <div style="color:#64748b;font-size:0.85em">
              <b style="color:#94a3b8">Financial Data</b><br>
              Yahoo Finance via yfinance. Free, real-time, no API key required.
            </div>
            <div style="color:#64748b;font-size:0.85em">
              <b style="color:#94a3b8">Historical P/E / PEG</b><br>
              Calculated from up to 4 years of available financials (labeled "4yr avg").
            </div>
            <div style="color:#64748b;font-size:0.85em">
              <b style="color:#94a3b8">AI Analysis</b><br>
              OpenAI Responses API with web_search_preview. Requires your API key.
            </div>
            <div style="color:#64748b;font-size:0.85em">
              <b style="color:#94a3b8">Non-US Tickers</b><br>
              Supported but some fields may be missing. A warning is shown.
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
