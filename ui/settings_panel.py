"""
Settings page: API key management, model selection, cache controls.
Keys are stored in ~/.talguard/settings.json — never in the project directory.
"""

import json
import os

import streamlit as st

from config import SETTINGS_PATH, AI_MODELS, DEFAULT_AI_MODEL


def _load_settings() -> dict:
    if not os.path.exists(SETTINGS_PATH):
        return {}
    try:
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_settings(settings: dict):
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)


def render_settings():
    st.title("Settings")

    settings = _load_settings()

    # ── AI Settings ──────────────────────────────────────────────────────────
    st.subheader("AI Settings")
    st.markdown(
        "The AI analysis evaluates 5 qualitative criteria using OpenAI with web search. "
        "Your API key is stored locally at `~/.talguard/settings.json` and never leaves your machine."
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        api_key_input = st.text_input(
            "OpenAI API Key",
            value=settings.get("openai_api_key", ""),
            type="password",
            placeholder="sk-...",
            help="Get your key at platform.openai.com/api-keys",
        )
    with col2:
        st.write("")
        st.write("")
        save_key = st.button("Save Key", use_container_width=True)

    model_options = list(AI_MODELS.keys())
    model_labels = list(AI_MODELS.values())
    current_model = settings.get("ai_model", DEFAULT_AI_MODEL)
    model_idx = model_options.index(current_model) if current_model in model_options else 0

    selected_model = st.selectbox(
        "Model",
        options=model_options,
        format_func=lambda k: AI_MODELS[k],
        index=model_idx,
        help="gpt-4o-mini is faster and cheaper. gpt-4o provides more thorough analysis.",
    )

    col_test, col_clear = st.columns(2)
    with col_test:
        test_key = st.button("Test API Key", use_container_width=True)
    with col_clear:
        clear_key = st.button("Remove API Key", use_container_width=True)

    if save_key:
        settings["openai_api_key"] = api_key_input.strip()
        settings["ai_model"] = selected_model
        _save_settings(settings)
        st.success("Settings saved.")

    if test_key:
        key_to_test = api_key_input.strip() or settings.get("openai_api_key", "")
        if not key_to_test:
            st.error("Enter an API key first.")
        else:
            with st.spinner("Testing API key..."):
                from ai.openai_client import test_api_key
                ok, msg = test_api_key(key_to_test)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    if clear_key:
        settings.pop("openai_api_key", None)
        _save_settings(settings)
        st.success("API key removed.")

    # Auto-save model selection on change
    if selected_model != settings.get("ai_model", DEFAULT_AI_MODEL):
        settings["ai_model"] = selected_model
        _save_settings(settings)

    st.divider()

    # ── Data Settings ─────────────────────────────────────────────────────────
    st.subheader("Data Settings")
    st.markdown("Financial data is fetched live from Yahoo Finance via yfinance.")

    from config import HISTORY_PATH
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r") as f:
                history = json.load(f)
            st.info(f"Analysis history: **{len(history)}** saved analyses")
        except Exception:
            st.info("Analysis history: unavailable")
    else:
        st.info("Analysis history: empty")

    if st.button("Clear Analysis History", use_container_width=False):
        if os.path.exists(HISTORY_PATH):
            os.remove(HISTORY_PATH)
        st.success("History cleared.")

    st.divider()

    # ── About ─────────────────────────────────────────────────────────────────
    st.subheader("About")
    st.markdown(
        """
**Talguard Investment Screener** digitalizes the 23-point Talguard quality/value checklist.

- **16 / 23 points** required to pass
- **17 quantitative criteria** auto-evaluated from Yahoo Finance
- **5 qualitative criteria** evaluated by OpenAI with web search
- **1 manual criterion** answered by the analyst

Data source: Yahoo Finance via [yfinance](https://github.com/ranaroussi/yfinance)
AI: OpenAI Responses API with `web_search_preview`
        """
    )
