"""
OpenAI Responses API wrapper with web_search_preview tool.
Runs all 5 qualitative criteria concurrently via asyncio.
"""

import asyncio
import json
import logging
import time
from typing import Optional

from ai.prompts import PROMPT_BUILDERS, SYSTEM_MESSAGE
from core.models import CompanyData

logger = logging.getLogger(__name__)

# Criteria that require AI evaluation
AI_CRITERIA_IDS = [1, 12, 13, 15, 20]


def _load_api_key() -> Optional[str]:
    """
    Load the OpenAI API key. Priority order:
      1. ~/.talguard/settings.json  (local / cloud user-entered key)
      2. st.secrets["OPENAI_API_KEY"]  (Streamlit Community Cloud secrets)
      3. OPENAI_API_KEY environment variable
    """
    import os
    from config import SETTINGS_PATH
    # 1. Local settings file
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r") as f:
                settings = json.load(f)
            key = settings.get("openai_api_key")
            if key:
                return key
        except Exception:
            pass
    # 2. Streamlit secrets (Streamlit Community Cloud)
    try:
        import streamlit as st
        key = st.secrets.get("OPENAI_API_KEY")
        if key:
            return key
    except Exception:
        pass
    # 3. Environment variable
    return os.environ.get("OPENAI_API_KEY") or None


def _load_model() -> str:
    """Load the selected model from settings, default to gpt-4o-mini."""
    import os
    from config import SETTINGS_PATH, DEFAULT_AI_MODEL
    if not os.path.exists(SETTINGS_PATH):
        return DEFAULT_AI_MODEL
    try:
        with open(SETTINGS_PATH, "r") as f:
            settings = json.load(f)
        return settings.get("ai_model") or DEFAULT_AI_MODEL
    except Exception:
        return DEFAULT_AI_MODEL


def _parse_json_response(text: str) -> Optional[dict]:
    """Extract JSON from the AI response text."""
    text = text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object within the text
        import re
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return None


async def _call_with_retry(
    client,
    model: str,
    criterion_id: int,
    user_prompt: str,
    max_retries: int = 3,
) -> Optional[dict]:
    """Call the OpenAI Responses API with web_search_preview, with retries."""
    delay = 1.0
    last_error = None

    for attempt in range(max_retries):
        try:
            response = await client.responses.create(
                model=model,
                tools=[{"type": "web_search_preview"}],
                input=[
                    {"role": "system", "content": SYSTEM_MESSAGE},
                    {"role": "user",   "content": user_prompt},
                ],
            )

            # Extract text output from response.
            # Structure: response.output → list of items; message items have
            # item.content → list of content blocks; text blocks have block.text.
            output_text = ""
            for item in response.output:
                item_type = getattr(item, "type", "")
                if item_type == "message":
                    for block in getattr(item, "content", []):
                        if getattr(block, "type", "") == "output_text":
                            output_text += getattr(block, "text", "")
                # Skip web_search_call, reasoning, and other non-text items

            if not output_text:
                logger.warning("Criterion %d: empty response on attempt %d", criterion_id, attempt + 1)
                await asyncio.sleep(delay)
                delay *= 2
                continue

            parsed = _parse_json_response(output_text)
            if parsed is None:
                logger.warning("Criterion %d: could not parse JSON on attempt %d", criterion_id, attempt + 1)
                last_error = f"Could not parse JSON from response: {output_text[:200]}"
                await asyncio.sleep(delay)
                delay *= 2
                continue

            return parsed

        except Exception as exc:
            last_error = str(exc)
            logger.warning("Criterion %d: API error on attempt %d: %s", criterion_id, attempt + 1, exc)
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
                delay *= 2

    logger.error("Criterion %d: all retries failed. Last error: %s", criterion_id, last_error)
    return {"error": last_error}


async def _run_all_async(data: CompanyData, api_key: str, model: str) -> dict:
    """Run all 5 AI criteria concurrently."""
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=api_key)

    tasks = {}
    for cid in AI_CRITERIA_IDS:
        builder = PROMPT_BUILDERS.get(cid)
        if builder is None:
            continue
        prompt = builder(data)
        tasks[cid] = _call_with_retry(client, model, cid, prompt)

    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    output = {}
    for cid, result in zip(tasks.keys(), results):
        if isinstance(result, Exception):
            output[cid] = {"error": str(result)}
        else:
            output[cid] = result

    return output


def run_ai_analysis(data: CompanyData, progress_callback=None) -> dict:
    """
    Synchronous entry point for Streamlit.
    Returns dict mapping criterion_id → parsed AI response dict.
    Returns empty dict {} if API key is not configured.
    """
    api_key = _load_api_key()
    if not api_key:
        return {}

    model = _load_model()

    if progress_callback:
        progress_callback(f"Running AI analysis with {model} + web search...")

    try:
        # Run the async event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(_run_all_async(data, api_key, model))
        loop.close()
        return results
    except Exception as exc:
        logger.error("AI analysis failed: %s", exc)
        return {}


def test_api_key(api_key: str) -> tuple[bool, str]:
    """
    Test an API key with a minimal call.
    Returns (success: bool, message: str).
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        # Minimal call using the chat completions API to verify the key
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Reply with: OK"}],
            max_tokens=5,
        )
        text = resp.choices[0].message.content or ""
        if text:
            return True, "API key is valid."
        return False, "API key valid but received empty response."
    except Exception as exc:
        return False, f"API key test failed: {exc}"
