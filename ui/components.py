"""
Reusable Streamlit UI components with professional dark-mode design.
"""

import streamlit as st

from config import CRITERIA_CONFIG, PASSING_SCORE, TOTAL_CRITERIA
from core.models import (
    CriterionResult,
    ScreenerResult,
    STATUS_PASS,
    STATUS_FAIL,
    STATUS_INSUFFICIENT_DATA,
    STATUS_NO_AI,
    STATUS_PENDING_MANUAL,
)

# ── Design tokens ─────────────────────────────────────────────────────────────

C_PASS    = "#10b981"   # emerald green
C_FAIL    = "#ef4444"   # red
C_WARN    = "#f59e0b"   # amber  (insufficient data)
C_MUTED   = "#6b7280"   # gray   (no AI key)
C_PENDING = "#3b82f6"   # blue   (manual pending)
C_CARD    = "#111827"   # card background
C_BORDER  = "#1f2937"   # card border
C_TEXT    = "#f1f5f9"   # primary text
C_TEXT2   = "#94a3b8"   # secondary text
C_TEXT3   = "#475569"   # muted text

STATUS_COLORS = {
    STATUS_PASS:              C_PASS,
    STATUS_FAIL:              C_FAIL,
    STATUS_INSUFFICIENT_DATA: C_WARN,
    STATUS_NO_AI:             C_MUTED,
    STATUS_PENDING_MANUAL:    C_PENDING,
}

STATUS_LABELS = {
    STATUS_PASS:              "PASS",
    STATUS_FAIL:              "FAIL",
    STATUS_INSUFFICIENT_DATA: "NO DATA",
    STATUS_NO_AI:             "NO AI KEY",
    STATUS_PENDING_MANUAL:    "PENDING",
}

STATUS_ICONS = {
    STATUS_PASS:              "✓",
    STATUS_FAIL:              "✗",
    STATUS_INSUFFICIENT_DATA: "?",
    STATUS_NO_AI:             "—",
    STATUS_PENDING_MANUAL:    "…",
}


def _fmt_market_cap(mc) -> str:
    if not mc:
        return "N/A"
    if mc >= 1e12:
        return f"${mc/1e12:.2f}T"
    if mc >= 1e9:
        return f"${mc/1e9:.1f}B"
    return f"${mc/1e6:.0f}M"


def _badge(status: str) -> str:
    color = STATUS_COLORS.get(status, C_MUTED)
    label = STATUS_LABELS.get(status, status)
    icon  = STATUS_ICONS.get(status, "")
    return (
        f'<span style="display:inline-flex;align-items:center;gap:4px;'
        f'background:{color}22;color:{color};border:1px solid {color}66;'
        f'padding:2px 10px;border-radius:20px;font-size:0.75em;font-weight:700;'
        f'letter-spacing:0.05em">{icon} {label}</span>'
    )


# ── Company header ─────────────────────────────────────────────────────────────

def render_company_header(result: ScreenerResult):
    mc_str = _fmt_market_cap(result.market_cap)
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#111827 0%,#1e293b 100%);
                    border:1px solid {C_BORDER};border-radius:12px;
                    padding:24px 28px;margin-bottom:20px;position:relative;overflow:hidden">
          <div style="position:absolute;top:0;right:0;width:200px;height:100%;
                      background:linear-gradient(90deg,transparent,#3b82f610);pointer-events:none"></div>
          <div style="font-size:0.75em;letter-spacing:0.12em;color:{C_TEXT3};
                      text-transform:uppercase;margin-bottom:6px">
            Company Analysis
          </div>
          <div style="font-size:1.8em;font-weight:800;color:{C_TEXT};line-height:1.1">
            {result.company_name}
            <span style="font-size:0.45em;font-weight:500;color:{C_TEXT3};
                         background:{C_BORDER};padding:3px 10px;border-radius:6px;
                         margin-left:10px;vertical-align:middle">{result.ticker}</span>
          </div>
          <div style="margin-top:10px;display:flex;gap:20px;flex-wrap:wrap">
            <span style="color:{C_TEXT2};font-size:0.9em">
              <span style="color:{C_TEXT3}">Sector</span>&nbsp; {result.sector}
            </span>
            <span style="color:{C_TEXT3}">·</span>
            <span style="color:{C_TEXT2};font-size:0.9em">
              <span style="color:{C_TEXT3}">Industry</span>&nbsp; {result.industry}
            </span>
            <span style="color:{C_TEXT3}">·</span>
            <span style="color:{C_TEXT2};font-size:0.9em">
              <span style="color:{C_TEXT3}">Market Cap</span>&nbsp; {mc_str}
            </span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Score gauge ────────────────────────────────────────────────────────────────

def render_score_gauge(result: ScreenerResult):
    score   = result.total_points
    max_pts = TOTAL_CRITERIA
    pct     = score / max_pts
    passed  = result.passed
    color   = C_PASS if passed else C_FAIL
    verdict = "PASS" if passed else "FAIL"
    needed  = max(0, PASSING_SCORE - score)

    bar_pct = int(pct * 100)

    # Mini breakdown
    n_pass  = sum(1 for c in result.criteria if c.status == STATUS_PASS)
    n_fail  = sum(1 for c in result.criteria if c.status == STATUS_FAIL)
    n_nodat = sum(1 for c in result.criteria if c.status in (STATUS_INSUFFICIENT_DATA, STATUS_NO_AI))

    st.markdown(
        f"""
        <div style="background:{C_CARD};border:1px solid {C_BORDER};border-radius:12px;
                    padding:24px 28px;margin-bottom:20px">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px">
            <div>
              <div style="font-size:0.75em;letter-spacing:0.12em;color:{C_TEXT3};
                          text-transform:uppercase;margin-bottom:8px">Total Score</div>
              <div style="display:flex;align-items:baseline;gap:8px">
                <span style="font-size:3.5em;font-weight:800;color:{color};line-height:1">{score}</span>
                <span style="font-size:1.3em;color:{C_TEXT3}">/ {max_pts}</span>
              </div>
              <div style="color:{C_TEXT3};font-size:0.85em;margin-top:4px">
                Need {PASSING_SCORE} to pass
                {"&nbsp;· " + str(needed) + " more needed" if not passed else "&nbsp;· All criteria met"}
              </div>
            </div>
            <div style="text-align:right">
              <div style="background:{color}20;color:{color};border:2px solid {color};
                          padding:10px 28px;border-radius:10px;font-size:1.4em;
                          font-weight:800;letter-spacing:0.08em">{verdict}</div>
            </div>
          </div>
          <div style="margin-top:20px">
            <div style="background:{C_BORDER};border-radius:99px;height:8px;overflow:hidden">
              <div style="background:linear-gradient(90deg,{color}aa,{color});
                          width:{bar_pct}%;height:100%;border-radius:99px;
                          transition:width 0.5s ease"></div>
            </div>
          </div>
          <div style="display:flex;gap:20px;margin-top:14px;flex-wrap:wrap">
            <span style="font-size:0.85em;color:{C_PASS}">
              <b>{n_pass}</b> passed
            </span>
            <span style="font-size:0.85em;color:{C_FAIL}">
              <b>{n_fail}</b> failed
            </span>
            <span style="font-size:0.85em;color:{C_WARN}">
              <b>{n_nodat}</b> no data / no AI
            </span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Criterion card ─────────────────────────────────────────────────────────────

def render_criterion_card(cr: CriterionResult):
    cfg_entry = CRITERIA_CONFIG.get(cr.criterion_id, {})
    ctype     = cfg_entry.get("type", "")
    color     = STATUS_COLORS.get(cr.status, C_MUTED)
    badge_html = _badge(cr.status)

    type_labels = {"quant": "Quantitative", "ai": "AI · Web Search", "manual": "Manual"}
    type_colors = {"quant": "#6366f1", "ai": "#8b5cf6", "manual": "#f59e0b"}
    type_label = type_labels.get(ctype, "")
    type_color = type_colors.get(ctype, C_TEXT3)

    value_html = ""
    if cr.actual_display:
        value_html = (
            f'<span style="color:{C_TEXT};font-weight:600">{cr.actual_display}</span>'
            + (f'<span style="color:{C_TEXT3}"> &nbsp;·&nbsp; threshold: {cr.threshold_display}</span>'
               if cr.threshold_display else "")
        )
    elif cr.threshold_display and cr.status != STATUS_PENDING_MANUAL:
        value_html = f'<span style="color:{C_TEXT3}">Threshold: {cr.threshold_display}</span>'

    with st.container():
        st.markdown(
            f"""
            <div style="display:flex;align-items:stretch;margin-bottom:6px;border-radius:8px;
                        overflow:hidden;border:1px solid {C_BORDER}">
              <div style="width:4px;background:{color};flex-shrink:0"></div>
              <div style="flex:1;background:{C_CARD};padding:11px 16px;
                          display:flex;justify-content:space-between;align-items:center;gap:12px">
                <div style="flex:1;min-width:0">
                  <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                    <span style="font-weight:600;color:{C_TEXT};font-size:0.95em">
                      #{cr.criterion_id}. {cr.name}
                    </span>
                    <span style="font-size:0.7em;color:{type_color};background:{type_color}18;
                                 padding:1px 7px;border-radius:20px;white-space:nowrap">
                      {type_label}
                    </span>
                  </div>
                  {f'<div style="margin-top:3px;font-size:0.85em">{value_html}</div>' if value_html else ''}
                </div>
                <div style="flex-shrink:0">{badge_html}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if cr.ai_reasoning or cr.error_message:
            with st.expander("View details", expanded=False):
                if cr.ai_score is not None:
                    conf_str = f"  ·  Confidence: **{cr.ai_confidence}**" if cr.ai_confidence else ""
                    st.markdown(f"**Moat Score: {cr.ai_score} / 10**{conf_str}")
                elif cr.ai_confidence:
                    st.markdown(f"*AI confidence: {cr.ai_confidence}*")
                if cr.ai_reasoning:
                    st.markdown(cr.ai_reasoning)
                if cr.error_message:
                    st.caption(f"ℹ {cr.error_message}")


# ── Section header ─────────────────────────────────────────────────────────────

def render_section_header(title: str, score: int, total: int, icon: str = ""):
    pct = score / total if total else 0
    bar_color = C_PASS if pct >= 0.7 else (C_WARN if pct >= 0.4 else C_FAIL)
    st.markdown(
        f"""
        <div style="margin:24px 0 10px 0">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <div style="font-size:0.7em;letter-spacing:0.14em;text-transform:uppercase;
                        color:{C_TEXT3};font-weight:600">{icon} {title}</div>
            <div style="font-size:0.8em;color:{bar_color};font-weight:700">{score}/{total}</div>
          </div>
          <div style="height:2px;background:{C_BORDER};border-radius:99px">
            <div style="width:{int(pct*100)}%;height:100%;background:{bar_color};
                        border-radius:99px"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
