"""
Talguard Investment Screener — Main Streamlit Application

Run with:  streamlit run app.py
"""

import os
import json

import streamlit as st

# ── Page config must be the very first Streamlit call ─────────────────────────
st.set_page_config(
    page_title="Talguard Investment Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
# Forces dark theme regardless of system setting and adds polish.
st.markdown(
    """
    <style>
    /* ── Root / app background ───────────────────────────── */
    html, body, [data-testid="stApp"], .stApp {
        background-color: #0a0f1e !important;
        color: #f1f5f9 !important;
    }

    /* ── Sidebar ─────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: #070c18 !important;
        border-right: 1px solid #1f2937 !important;
    }
    [data-testid="stSidebar"] * { color: #f1f5f9; }

    /* ── Inputs ──────────────────────────────────────────── */
    [data-testid="stTextInput"] input,
    [data-testid="stSelectbox"] select,
    textarea {
        background-color: #111827 !important;
        color: #f1f5f9 !important;
        border-color: #1f2937 !important;
        border-radius: 8px !important;
    }
    [data-testid="stTextInput"] input:focus { border-color: #3b82f6 !important; }

    /* ── Buttons ─────────────────────────────────────────── */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.15s ease !important;
        border: 1px solid #1f2937 !important;
        background-color: #111827 !important;
        color: #f1f5f9 !important;
    }
    .stButton > button:hover { border-color: #3b82f6 !important; color: #3b82f6 !important; }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        color: #fff !important;
        border-color: transparent !important;
    }
    .stButton > button[kind="primary"]:hover { filter: brightness(1.1) !important; }

    /* ── Expanders ───────────────────────────────────────── */
    [data-testid="stExpander"] {
        background-color: #0f172a !important;
        border: 1px solid #1f2937 !important;
        border-radius: 8px !important;
    }

    /* ── Progress ────────────────────────────────────────── */
    .stProgress > div > div { background-color: #3b82f6 !important; }

    /* ── Download buttons ────────────────────────────────── */
    [data-testid="stDownloadButton"] button {
        background-color: #111827 !important;
        border-color: #1f2937 !important;
        color: #94a3b8 !important;
        font-size: 0.85em !important;
    }

    /* ── Dividers ────────────────────────────────────────── */
    hr { border-color: #1f2937 !important; }

    /* ── Info / success / warning banners ────────────────── */
    [data-testid="stAlert"] { border-radius: 8px !important; }

    /* ── Remove default Streamlit top padding ────────────── */
    .block-container { padding-top: 1.5rem !important; }

    /* ── Radio buttons ───────────────────────────────────── */
    [data-testid="stRadio"] label { color: #f1f5f9 !important; }
    [data-testid="stRadio"] > div { gap: 4px !important; }

    /* ── Captions ────────────────────────────────────────── */
    .stCaption, [data-testid="stCaption"] { color: #475569 !important; }

    /* ── Hide streamlit menu / footer ────────────────────── */
    #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Session state ─────────────────────────────────────────────────────────────
_DEFAULTS = {
    "page":            "home",
    "screener_result": None,
    "company_data":    None,
    "ai_results":      {},
    "last_ticker":     "",
    "pending_ticker":  None,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── Detect API key ────────────────────────────────────────────────────────────
from config import SETTINGS_PATH
_has_key = False
if os.path.exists(SETTINGS_PATH):
    try:
        with open(SETTINGS_PATH) as _f:
            _s = json.load(_f)
        _has_key = bool(_s.get("openai_api_key"))
    except Exception:
        pass


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown(
        """
        <div style="padding:20px 4px 16px 4px">
          <div style="font-size:1.3em;font-weight:900;color:#f1f5f9;letter-spacing:-0.02em">
            📈 Talguard
          </div>
          <div style="font-size:0.72em;color:#475569;letter-spacing:0.08em;
                      text-transform:uppercase;margin-top:2px">
            Investment Screener
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Ticker input
    ticker_input = st.text_input(
        "ticker",
        value=st.session_state.get("pending_ticker") or st.session_state["last_ticker"],
        placeholder="Ticker symbol…",
        label_visibility="collapsed",
    ).strip().upper()

    analyze_btn = st.button("Analyze Company", use_container_width=True, type="primary")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Navigation
    _pages = {
        "home":      "🏠  Home",
        "analysis":  "🔍  Screener",
        "portfolio": "📋  Portfolio",
        "history":   "🕐  History",
        "about":     "📖  About",
        "settings":  "⚙️  Settings",
    }

    for page_key, page_label in _pages.items():
        is_active = st.session_state["page"] == page_key
        style = (
            "background:#1e3a5f;color:#60a5fa;border-radius:8px;padding:8px 14px;"
            "margin-bottom:2px;font-weight:600;font-size:0.9em;cursor:pointer;display:block;"
            "border:1px solid #2563eb33"
        ) if is_active else (
            "color:#94a3b8;border-radius:8px;padding:8px 14px;margin-bottom:2px;"
            "font-size:0.9em;cursor:pointer;display:block;border:1px solid transparent"
        )
        if st.button(page_label, key=f"nav_{page_key}", use_container_width=True):
            st.session_state["page"] = page_key
            if page_key != "analysis":
                st.session_state["pending_ticker"] = None
            st.rerun()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown('<hr style="border-color:#1f2937;margin:0">', unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # AI status
    if _has_key:
        st.markdown(
            '<div style="font-size:0.78em;color:#10b981;background:#10b98115;'
            'border:1px solid #10b98133;border-radius:6px;padding:6px 10px">'
            '🤖 AI analysis active</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="font-size:0.78em;color:#f59e0b;background:#f59e0b15;'
            'border:1px solid #f59e0b33;border-radius:6px;padding:6px 10px">'
            '⚠ AI not configured — add key in Settings</div>',
            unsafe_allow_html=True,
        )


# ── Run analysis ──────────────────────────────────────────────────────────────
def run_analysis(ticker: str):
    from core.data_fetcher import fetch_all
    from core.criteria_evaluator import evaluate_all
    from ai.openai_client import run_ai_analysis
    from storage.history import save_result
    from storage.portfolio import update_from_result, is_in_portfolio

    st.session_state["screener_result"] = None
    st.session_state["pending_ticker"]  = None

    with st.spinner(f"Fetching financial data for {ticker}…"):
        data = fetch_all(ticker)

    if not data.is_valid:
        st.error(f"Ticker **{ticker}** not found. Check the symbol and try again.")
        return

    if data.info.get("country") and data.info.get("country") != "United States":
        st.warning(
            f"{ticker} is listed outside the US ({data.info.get('country')}). "
            "Some financial fields may be unavailable.",
            icon="🌐",
        )

    st.session_state["company_data"] = data

    if _has_key:
        with st.spinner("Running AI analysis with live web search (≈15s)…"):
            ai_results = run_ai_analysis(data)
    else:
        ai_results = {}

    st.session_state["ai_results"] = ai_results

    result = evaluate_all(data, ai_results, manual_answer_21=None)
    st.session_state["screener_result"] = result
    st.session_state["last_ticker"]     = ticker
    st.session_state["page"]            = "analysis"

    save_result(result.to_dict())
    if is_in_portfolio(ticker):
        update_from_result(result.to_dict())


# Trigger analysis
if analyze_btn and ticker_input:
    run_analysis(ticker_input)
elif st.session_state.get("pending_ticker"):
    _pt = st.session_state["pending_ticker"]
    st.session_state["pending_ticker"] = None
    run_analysis(_pt)


# ── Page routing ──────────────────────────────────────────────────────────────
page = st.session_state["page"]

# ── HOME ──────────────────────────────────────────────────────────────────────
if page == "home":
    st.markdown(
        """
        <div style="max-width:720px;margin:40px auto 0 auto;text-align:center;padding:0 20px">
          <div style="font-size:0.75em;letter-spacing:0.14em;text-transform:uppercase;
                      color:#3b82f6;font-weight:600;margin-bottom:12px">
            Professional Investment Analysis
          </div>
          <h1 style="font-size:2.6em;font-weight:900;color:#f1f5f9;
                     line-height:1.15;margin:0 0 16px 0">
            Find Quality Stocks<br>With Confidence
          </h1>
          <p style="color:#94a3b8;font-size:1.1em;line-height:1.7;margin-bottom:36px">
            The Talguard 23-point system combines quantitative financial analysis with
            AI-powered qualitative research to identify high-quality businesses at reasonable valuations.
          </p>
          <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap">
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        cta_ticker = st.text_input(
            "cta_ticker",
            placeholder="Enter a ticker to get started…",
            label_visibility="collapsed",
            key="home_ticker",
        ).strip().upper()
        if st.button("Analyze Company", use_container_width=True, type="primary", key="home_analyze"):
            if cta_ticker:
                run_analysis(cta_ticker)
            else:
                st.error("Enter a ticker symbol first.")

    st.markdown(
        """
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Feature grid
    st.markdown("<div style='height:56px'></div>", unsafe_allow_html=True)
    feat_col1, feat_col2, feat_col3 = st.columns(3)
    features = [
        ("📊", "17 Quantitative Criteria",
         "Margins, FCF, debt ratios, P/E, PEG, ROE, buybacks, dividends — auto-evaluated from Yahoo Finance."),
        ("🤖", "AI Qualitative Analysis",
         "5 criteria scored by GPT with live web search: competitive moat, market leadership, management integrity, and more."),
        ("📋", "Portfolio Tracking",
         "Add companies to your watchlist, track scores over time, and compare holdings side-by-side."),
    ]
    for col, (icon, title, desc) in zip([feat_col1, feat_col2, feat_col3], features):
        with col:
            st.markdown(
                f"""
                <div style="background:#111827;border:1px solid #1f2937;border-radius:12px;
                            padding:24px;text-align:center;height:100%">
                  <div style="font-size:2em;margin-bottom:12px">{icon}</div>
                  <div style="font-weight:700;color:#f1f5f9;font-size:1em;margin-bottom:8px">{title}</div>
                  <div style="color:#64748b;font-size:0.87em;line-height:1.6">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Score threshold callout
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#1e3a5f,#1e1b4b);
                    border:1px solid #3b82f633;border-radius:12px;
                    padding:28px;text-align:center;max-width:600px;margin:0 auto">
          <div style="font-size:2.8em;font-weight:900;color:#3b82f6;line-height:1">16 / 23</div>
          <div style="color:#94a3b8;margin-top:8px;font-size:1em">
            Points required to pass the Talguard quality threshold
          </div>
          <div style="color:#475569;margin-top:6px;font-size:0.85em">
            1 point per criterion · 17 auto-scored · 5 AI-scored · 1 manual
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── ANALYSIS ──────────────────────────────────────────────────────────────────
elif page == "analysis":
    result = st.session_state.get("screener_result")
    data   = st.session_state.get("company_data")
    ai_res = st.session_state.get("ai_results", {})

    if result is None:
        st.markdown(
            """
            <div style="text-align:center;padding:80px 20px">
              <div style="font-size:3em;margin-bottom:16px">🔍</div>
              <div style="font-size:1.3em;font-weight:700;color:#f1f5f9;margin-bottom:8px">
                No analysis yet
              </div>
              <div style="color:#64748b">
                Enter a ticker symbol in the sidebar and click <strong style="color:#3b82f6">Analyze Company</strong>.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        from ui.results_page import render_results
        render_results(result, data, ai_res)

# ── PORTFOLIO ─────────────────────────────────────────────────────────────────
elif page == "portfolio":
    from ui.portfolio_page import render_portfolio
    render_portfolio()

# ── HISTORY ───────────────────────────────────────────────────────────────────
elif page == "history":
    from storage.history import load_history
    st.markdown(
        """
        <div style="margin-bottom:28px">
          <div style="font-size:0.75em;letter-spacing:0.14em;text-transform:uppercase;
                      color:#475569;margin-bottom:6px">Archive</div>
          <h1 style="font-size:1.9em;font-weight:800;color:#f1f5f9;margin:0">Analysis History</h1>
          <p style="color:#64748b;margin-top:6px;font-size:0.95em">
            All companies you have analyzed, most recent first.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    records = load_history()
    if not records:
        st.markdown(
            """
            <div style="background:#111827;border:1px solid #1f2937;border-radius:12px;
                        padding:48px;text-align:center">
              <div style="font-size:2em;margin-bottom:12px">🕐</div>
              <div style="font-size:1.1em;font-weight:600;color:#f1f5f9;margin-bottom:6px">No history yet</div>
              <div style="color:#475569;font-size:0.9em">Analyze a company to see results here.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Column headers
        st.markdown(
            '<div style="display:grid;grid-template-columns:1fr 2fr 1fr 1fr 1fr;'
            'gap:8px;padding:6px 12px;margin-bottom:4px">'
            + "".join(
                f'<div style="font-size:0.7em;letter-spacing:0.1em;text-transform:uppercase;'
                f'color:#475569;font-weight:600">{h}</div>'
                for h in ["Ticker", "Company", "Score", "Result", "Date"]
            )
            + "</div>",
            unsafe_allow_html=True,
        )

        for r in records:
            ticker  = r.get("ticker", "")
            company = r.get("company_name", "")
            score   = r.get("total_points", 0)
            passed  = r.get("passed", False)
            date    = r.get("analysis_date", "")[:10]

            score_color   = "#10b981" if passed else "#ef4444"
            result_badge  = (
                f'<span style="background:#10b98120;color:#10b981;border:1px solid #10b98144;'
                f'padding:2px 10px;border-radius:20px;font-size:0.78em;font-weight:700">✓ PASS</span>'
                if passed else
                f'<span style="background:#ef444420;color:#ef4444;border:1px solid #ef444444;'
                f'padding:2px 10px;border-radius:20px;font-size:0.78em;font-weight:700">✗ FAIL</span>'
            )

            col_t, col_c, col_s, col_r, col_d = st.columns([1, 2, 1, 1, 1])
            with col_t:
                st.markdown(
                    f'<div style="background:#1f2937;padding:3px 10px;border-radius:6px;'
                    f'font-weight:700;color:#f1f5f9;font-size:0.9em;display:inline-block">{ticker}</div>',
                    unsafe_allow_html=True,
                )
            with col_c:
                st.markdown(f'<div style="color:#94a3b8;font-size:0.88em;padding:4px 0">{company}</div>', unsafe_allow_html=True)
            with col_s:
                st.markdown(f'<div style="font-weight:700;color:{score_color};font-size:0.9em;padding:4px 0">{score}/23</div>', unsafe_allow_html=True)
            with col_r:
                st.markdown(f'<div style="padding:2px 0">{result_badge}</div>', unsafe_allow_html=True)
            with col_d:
                st.markdown(f'<div style="color:#475569;font-size:0.82em;padding:4px 0">{date}</div>', unsafe_allow_html=True)

            st.markdown('<hr style="border-color:#1f2937;margin:4px 0">', unsafe_allow_html=True)

        st.markdown(f'<div style="color:#475569;font-size:0.8em;margin-top:8px">{len(records)} analyses saved</div>', unsafe_allow_html=True)

# ── ABOUT ─────────────────────────────────────────────────────────────────────
elif page == "about":
    from ui.about_page import render_about
    render_about()

# ── SETTINGS ─────────────────────────────────────────────────────────────────
elif page == "settings":
    from ui.settings_panel import render_settings
    render_settings()
