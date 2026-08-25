"""
Thin wrapper around the Gemini API (Google AI Studio, free tier).

Reads GEMINI_API_KEY from environment (loaded from .env via python-dotenv).

Free-tier quota note (checked 2026-08-25 via aistudio.google.com/rate-limit,
not publicly documented so re-check there if these seem off):
  gemini-3.7-flash        RPM 5   RPD 20    <- do not use as default, nearly exhausted
  gemini-2.5-flash        RPM 5   RPD 20
  gemini-2.5-flash-lite   RPM 10  RPD 20
  gemini-3.1-flash-lite   RPM 15  RPD 500   <- default, most headroom
  gemini-3.5-flash-lite   RPM 15  RPD 500   <- good second model for benchmark comparison
Default model is gemini-3.1-flash-lite for this reason: 500/day comfortably
covers dev iteration plus the full ~41-scenario benchmark across a few models.

RPD (requests per day) is a hard daily cap, not transient like RPM. Retrying
a 429 caused by RPD exhaustion wastes remaining quota and will never succeed
until the daily reset, so this wrapper only retries when the error message
signals a per-minute limit; an RPD-exhaustion 429 raises immediately with a
clear message instead of burning retries.
"""

import json
import os
import time

try:
    from google import genai
except ImportError:
    genai = None

_client = None


def _get_client():
    global _client
    if _client is None:
        if genai is None:
            raise ImportError(
                "Missing dependency. Run: pip install google-genai"
            )
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not set. Add it to .env (see .env.example)."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def _is_daily_quota_exhausted(error_str):
    return "perday" in error_str.replace(" ", "").replace("_", "").lower() or "requestsperday" in error_str.replace(" ", "").lower()


def call_gemini(prompt, model_name="gemini-3.1-flash-lite", max_retries=3):
    """
    Calls the given Gemini model with a plain text prompt, returns the raw
    text response. Retries on per-minute rate-limit (429) errors with
    exponential backoff. Fails fast (no retry) on daily quota exhaustion,
    since retrying that only wastes remaining quota.
    """
    client = _get_client()
    last_error = None

    for attempt in range(max_retries):
        try:
            start = time.monotonic()
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            latency_ms = int((time.monotonic() - start) * 1000)
            return response.text, latency_ms
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            is_429 = "429" in error_str or "rate" in error_str or "quota" in error_str
            if not is_429:
                raise
            if _is_daily_quota_exhausted(error_str):
                raise RuntimeError(
                    f"Daily free-tier quota exhausted for model '{model_name}'. "
                    f"Switch models or wait for the daily reset. Original error: {e}"
                )
            wait = 2 ** attempt * 5  # 5s, 10s, 20s
            time.sleep(wait)
            continue

    raise RuntimeError(f"Gemini call failed after {max_retries} retries: {last_error}")


def parse_json_response(raw_text):
    """
    Gemini sometimes wraps JSON in markdown code fences despite instructions.
    Strips those before parsing.
    """
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    return json.loads(text)
