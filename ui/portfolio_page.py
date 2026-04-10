"""
Portfolio page: track multiple tickers, see their latest scores at a glance.
"""

import streamlit as st

from storage.portfolio import (
    get_portfolio,
    add_ticker,
    remove_ticker,
    is_in_portfolio,
    update_from_result,
)

C_CARD   = "#111827"
C_BORDER = "#1f2937"
C_TEXT   = "#f1f5f9"
C_TEXT2  = "#94a3b8"
C_TEXT3  = "#475569"
C_PASS   = "#10b981"
C_FAIL   = "#ef4444"
C_WARN   = "#f59e0b"
C_BLUE   = "#3b82f6"


def _score_color(passed, score) -> str:
    if score is None:
        return C_TEXT3
    return C_PASS if passed else C_FAIL


def render_portfolio():
    st.markdown(
        """
        <div style="margin-bottom:28px">
          <div style="font-size:0.75em;letter-spacing:0.14em;text-transform:uppercase;
                      color:#475569;margin-bottom:6px">Watchlist</div>
          <h1 style="font-size:1.9em;font-weight:800;color:#f1f5f9;margin:0">
            Portfolio Tracker
          </h1>
          <p style="color:#64748b;margin-top:6px;font-size:0.95em">
            Track companies you follow. Analyze each one to update their Talguard score.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    portfolio = get_portfolio()

    # ── Add ticker ────────────────────────────────────────────────────────────
    with st.container():
        col_input, col_btn = st.columns([3, 1])
        with col_input:
            new_ticker = st.text_input(
                "Add to portfolio",
                placeholder="Enter ticker (e.g. AAPL, MSFT, KO)",
                label_visibility="collapsed",
                key="portfolio_add_input",
            ).strip().upper()
        with col_btn:
            if st.button("Add", use_container_width=True, type="primary"):
                if new_ticker:
                    if add_ticker(new_ticker):
                        st.success(f"{new_ticker} added to portfolio.")
                        st.rerun()
                    else:
                        st.warning(f"{new_ticker} is already in your portfolio.")
                else:
                    st.error("Enter a ticker symbol first.")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if not portfolio:
        st.markdown(
            f"""
            <div style="background:{C_CARD};border:1px solid {C_BORDER};border-radius:12px;
                        padding:48px;text-align:center;margin-top:16px">
              <div style="font-size:2em;margin-bottom:12px">📋</div>
              <div style="font-size:1.1em;font-weight:600;color:{C_TEXT};margin-bottom:6px">
                Your portfolio is empty
              </div>
              <div style="color:{C_TEXT3};font-size:0.9em">
                Add tickers above to start tracking companies.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ── Portfolio summary ─────────────────────────────────────────────────────
    analyzed    = [p for p in portfolio if p["last_score"] is not None]
    n_pass      = sum(1 for p in analyzed if p["last_passed"])
    n_fail      = len(analyzed) - n_pass
    n_unanalyzed = len(portfolio) - len(analyzed)

    if analyzed:
        avg_score = sum(p["last_score"] for p in analyzed) / len(analyzed)
    else:
        avg_score = None

    col1, col2, col3, col4 = st.columns(4)
    metric_style = f"background:{C_CARD};border:1px solid {C_BORDER};border-radius:10px;padding:16px 18px;text-align:center"

    with col1:
        st.markdown(
            f'<div style="{metric_style}">'
            f'<div style="font-size:1.8em;font-weight:800;color:{C_BLUE}">{len(portfolio)}</div>'
            f'<div style="color:{C_TEXT2};font-size:0.8em;margin-top:4px">Total Holdings</div>'
            f'</div>', unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f'<div style="{metric_style}">'
            f'<div style="font-size:1.8em;font-weight:800;color:{C_PASS}">{n_pass}</div>'
            f'<div style="color:{C_TEXT2};font-size:0.8em;margin-top:4px">Passing Score</div>'
            f'</div>', unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f'<div style="{metric_style}">'
            f'<div style="font-size:1.8em;font-weight:800;color:{C_FAIL}">{n_fail}</div>'
            f'<div style="color:{C_TEXT2};font-size:0.8em;margin-top:4px">Below Threshold</div>'
            f'</div>', unsafe_allow_html=True
        )
    with col4:
        avg_disp = f"{avg_score:.1f}/23" if avg_score is not None else "—"
        avg_color = C_PASS if avg_score and avg_score >= 16 else (C_FAIL if avg_score else C_TEXT3)
        st.markdown(
            f'<div style="{metric_style}">'
            f'<div style="font-size:1.8em;font-weight:800;color:{avg_color}">{avg_disp}</div>'
            f'<div style="color:{C_TEXT2};font-size:0.8em;margin-top:4px">Avg Score</div>'
            f'</div>', unsafe_allow_html=True
        )

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Holdings table ────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="font-size:0.7em;letter-spacing:0.14em;text-transform:uppercase;'
        f'color:{C_TEXT3};font-weight:600;margin-bottom:10px">Holdings</div>',
        unsafe_allow_html=True,
    )

    for item in portfolio:
        ticker  = item["ticker"]
        company = item.get("last_company") or ticker
        score   = item.get("last_score")
        passed  = item.get("last_passed")
        date    = item.get("last_analysis_date") or "Not analyzed"
        added   = item.get("added_date", "")

        score_color = _score_color(passed, score)
        score_disp  = f"{score}/23" if score is not None else "—"

        if passed is True:
            verdict_html = f'<span style="background:{C_PASS}20;color:{C_PASS};border:1px solid {C_PASS}44;padding:2px 10px;border-radius:20px;font-size:0.75em;font-weight:700">✓ PASS</span>'
        elif passed is False:
            verdict_html = f'<span style="background:{C_FAIL}20;color:{C_FAIL};border:1px solid {C_FAIL}44;padding:2px 10px;border-radius:20px;font-size:0.75em;font-weight:700">✗ FAIL</span>'
        else:
            verdict_html = f'<span style="background:{C_TEXT3}20;color:{C_TEXT3};border:1px solid {C_TEXT3}44;padding:2px 10px;border-radius:20px;font-size:0.75em;font-weight:600">— Unanalyzed</span>'

        col_info, col_score, col_actions = st.columns([4, 2, 2])

        with col_info:
            st.markdown(
                f"""
                <div style="background:{C_CARD};border:1px solid {C_BORDER};border-radius:8px;
                            padding:14px 18px;height:100%">
                  <div style="display:flex;align-items:center;gap:10px">
                    <div style="background:{C_BORDER};padding:4px 10px;border-radius:6px;
                                font-weight:800;color:{C_TEXT};font-size:0.95em">{ticker}</div>
                    <div style="font-weight:500;color:{C_TEXT2};font-size:0.9em">{company}</div>
                  </div>
                  <div style="margin-top:6px;display:flex;align-items:center;gap:12px">
                    {verdict_html}
                    <span style="color:{C_TEXT3};font-size:0.78em">Last analyzed: {date}</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_score:
            # Score bar
            bar_pct = int((score / 23) * 100) if score is not None else 0
            st.markdown(
                f"""
                <div style="background:{C_CARD};border:1px solid {C_BORDER};border-radius:8px;
                            padding:14px 18px;height:100%;display:flex;flex-direction:column;
                            justify-content:center">
                  <div style="font-size:1.5em;font-weight:800;color:{score_color}">{score_disp}</div>
                  <div style="height:4px;background:{C_BORDER};border-radius:99px;margin-top:6px">
                    <div style="width:{bar_pct}%;height:100%;background:{score_color};
                                border-radius:99px"></div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_actions:
            st.markdown(
                f'<div style="background:{C_CARD};border:1px solid {C_BORDER};border-radius:8px;'
                f'padding:10px 14px;height:100%;display:flex;flex-direction:column;gap:6px">',
                unsafe_allow_html=True,
            )
            if st.button("Analyze", key=f"analyze_{ticker}", use_container_width=True, type="primary"):
                st.session_state["page"] = "analysis"
                st.session_state["pending_ticker"] = ticker
                st.rerun()
            if st.button("Remove", key=f"remove_{ticker}", use_container_width=True):
                remove_ticker(ticker)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if n_unanalyzed > 0:
        st.caption(f"{n_unanalyzed} holding{'s' if n_unanalyzed > 1 else ''} not yet analyzed — click Analyze to score them.")
