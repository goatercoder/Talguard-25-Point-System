"""
Results page: renders the full ScreenerResult including the manual criterion flow.
"""

import streamlit as st

from core.models import ScreenerResult, STATUS_PASS, STATUS_FAIL, STATUS_PENDING_MANUAL
from core.criteria_evaluator import evaluate_all
from ui.components import (
    render_company_header,
    render_score_gauge,
    render_criterion_card,
    render_section_header,
)

C_CARD   = "#111827"
C_BORDER = "#1f2937"
C_TEXT3  = "#475569"
C_PASS   = "#10b981"
C_FAIL   = "#ef4444"
C_BLUE   = "#3b82f6"


def render_results(result: ScreenerResult, data, ai_results: dict):
    pending_21 = any(c.criterion_id == 21 and c.status == STATUS_PENDING_MANUAL for c in result.criteria)

    # ── Top action bar ────────────────────────────────────────────────────────
    from storage.portfolio import is_in_portfolio, add_ticker, update_from_result
    in_portfolio = is_in_portfolio(result.ticker)

    col_header, col_actions = st.columns([5, 2])
    with col_header:
        render_company_header(result)
    with col_actions:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if in_portfolio:
            st.markdown(
                f'<div style="background:{C_PASS}15;border:1px solid {C_PASS}44;'
                f'border-radius:8px;padding:10px 14px;color:{C_PASS};font-size:0.85em;'
                f'font-weight:600;text-align:center">✓ In Portfolio</div>',
                unsafe_allow_html=True,
            )
        else:
            if st.button("+ Add to Portfolio", use_container_width=True):
                add_ticker(result.ticker)
                update_from_result(result.to_dict())
                st.success(f"{result.ticker} added to portfolio.")
                st.rerun()

        if not pending_21:
            _render_export_row(result)

    if pending_21:
        st.info("Answer criterion #21 below to complete the analysis.", icon="✋")

    # Score gauge (full width)
    render_score_gauge(result)

    # ── Three column layout for criteria ──────────────────────────────────────
    col_main, col_side = st.columns([3, 1])

    with col_main:
        # Core
        core = result.core_criteria
        render_section_header("Core Checklist", sum(c.points for c in core), len(core), "◆")
        for cr in core:
            render_criterion_card(cr)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Additional
        additional = result.additional_criteria
        render_section_header("Additional Checklist", sum(c.points for c in additional), len(additional), "◇")
        for cr in additional:
            if cr.criterion_id == 21 and cr.status == STATUS_PENDING_MANUAL:
                _render_manual_criterion(data, ai_results)
            else:
                render_criterion_card(cr)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Valuation
        valuation = result.valuation_criteria
        render_section_header("Valuation", sum(c.points for c in valuation), len(valuation), "◈")
        for cr in valuation:
            render_criterion_card(cr)

    with col_side:
        _render_summary_panel(result)


def _render_manual_criterion(data, ai_results):
    st.markdown(
        f"""
        <div style="background:#1e293b;border:1px solid #3b82f644;border-left:4px solid #3b82f6;
                    border-radius:8px;padding:14px 16px;margin-bottom:6px">
          <div style="font-weight:600;color:#f1f5f9;font-size:0.95em">#21. Do You Understand the Company?</div>
          <div style="color:#64748b;font-size:0.83em;margin-top:2px">Manual · Analyst conviction</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    answer = st.radio(
        "Do you understand this business?",
        options=[
            "Yes — I understand the business model and competitive dynamics",
            "No — I need more research before making a decision",
        ],
        key="criterion_21_answer",
        label_visibility="collapsed",
    )
    if st.button("Submit Answer", key="submit_21", type="primary"):
        answered = answer.startswith("Yes")
        updated = evaluate_all(data, ai_results, manual_answer_21=answered)
        from storage.history import save_result
        from storage.portfolio import update_from_result
        st.session_state["screener_result"] = updated
        save_result(updated.to_dict())
        update_from_result(updated.to_dict())
        st.rerun()


def _render_summary_panel(result: ScreenerResult):
    """Right-side summary panel showing pass/fail breakdown."""
    st.markdown("<div style='height:56px'></div>", unsafe_allow_html=True)  # align with header

    total = result.total_points
    passed = result.passed
    color = C_PASS if passed else C_FAIL

    # Group scores
    core      = result.core_criteria
    add       = result.additional_criteria
    val       = result.valuation_criteria
    core_sc   = sum(c.points for c in core)
    add_sc    = sum(c.points for c in add)
    val_sc    = sum(c.points for c in val)

    st.markdown(
        f"""
        <div style="background:{C_CARD};border:1px solid {C_BORDER};border-radius:10px;
                    padding:18px;margin-bottom:12px;position:sticky;top:20px">
          <div style="font-size:0.7em;letter-spacing:0.12em;text-transform:uppercase;
                      color:{C_TEXT3};margin-bottom:12px">Score Breakdown</div>
          {_group_row("Core Checklist", core_sc, len(core))}
          {_group_row("Additional", add_sc, len(add))}
          {_group_row("Valuation", val_sc, len(val))}
          <div style="border-top:1px solid {C_BORDER};margin:12px 0"></div>
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="font-weight:700;color:#f1f5f9">Total</span>
            <span style="font-size:1.3em;font-weight:800;color:{color}">{total}/23</span>
          </div>
          <div style="margin-top:12px">
            <div style="height:6px;background:{C_BORDER};border-radius:99px">
              <div style="width:{int(total/23*100)}%;height:100%;background:{color};
                          border-radius:99px"></div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Status legend
    from config import TOTAL_CRITERIA
    from core.models import STATUS_INSUFFICIENT_DATA, STATUS_NO_AI
    n_pass  = sum(1 for c in result.criteria if c.status == STATUS_PASS)
    n_fail  = sum(1 for c in result.criteria if c.status == STATUS_FAIL)
    n_nodat = sum(1 for c in result.criteria if c.status in (STATUS_INSUFFICIENT_DATA, STATUS_NO_AI))
    n_pend  = sum(1 for c in result.criteria if c.status == STATUS_PENDING_MANUAL)

    rows = [
        (C_PASS,  "Passed",   n_pass),
        (C_FAIL,  "Failed",   n_fail),
        ("#f59e0b", "No Data", n_nodat),
    ]
    if n_pend:
        rows.append(("#3b82f6", "Pending", n_pend))

    rows_html = "".join(
        f'<div style="display:flex;justify-content:space-between;padding:4px 0">'
        f'<span style="color:{c};font-size:0.85em">{lbl}</span>'
        f'<span style="font-weight:600;color:{c};font-size:0.85em">{n}</span>'
        f'</div>'
        for c, lbl, n in rows
    )

    st.markdown(
        f"""
        <div style="background:{C_CARD};border:1px solid {C_BORDER};border-radius:10px;padding:16px 18px">
          <div style="font-size:0.7em;letter-spacing:0.12em;text-transform:uppercase;
                      color:{C_TEXT3};margin-bottom:10px">Criteria Status</div>
          {rows_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _group_row(label: str, score: int, total: int) -> str:
    pct = score / total if total else 0
    color = C_PASS if pct >= 0.7 else ("#f59e0b" if pct >= 0.4 else C_FAIL)
    return (
        f'<div style="display:flex;justify-content:space-between;padding:4px 0;'
        f'border-bottom:1px solid {C_BORDER};margin-bottom:4px">'
        f'<span style="color:#94a3b8;font-size:0.85em">{label}</span>'
        f'<span style="font-weight:600;color:{color};font-size:0.85em">{score}/{total}</span>'
        f'</div>'
    )


def _render_export_row(result: ScreenerResult):
    from storage.exporter import to_csv_bytes
    import json
    csv_bytes  = to_csv_bytes(result)
    json_bytes = json.dumps(result.to_dict(), indent=2).encode()
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "CSV",
            data=csv_bytes,
            file_name=f"{result.ticker}_talguard_{result.analysis_date.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "JSON",
            data=json_bytes,
            file_name=f"{result.ticker}_talguard_{result.analysis_date.strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True,
        )
