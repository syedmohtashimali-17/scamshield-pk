"""
utils/gemini.py
----------------
OWNER: Person 2 (AI Integration)

NOTE ON FILE NAME: This file is still called `gemini.py` (per the original
team spec / app.py import: `from utils import gemini`) but the underlying
AI provider is now GROQ, not Google Gemini. We switched because Google's
Gemini API keys generated in late 2026 use a new "Auth key" (AQ.) format
that was returning 401 ACCESS_TOKEN_TYPE_UNSUPPORTED errors — a widely
reported, unresolved issue on Google's side at the time of the hackathon.
Groq's API keys work immediately and its free tier is generous and fast.

Public contract (used by app.py and utils/risk_engine.py — DO NOT CHANGE):

    analyze_message(text: str, image_bytes: bytes | None = None) -> dict

Return shape (always this exact shape, even on failure):
{
    "risk_level": "Low" | "Suspicious" | "High",
    "risk_score": int (0-100),
    "scam_type": str,
    "red_flags": list[str],
    "explanation": str,
    "recommended_action": str,
    "roman_urdu_advice": str
}

Setup:
    - Get a free key at https://console.groq.com/keys
    - Set the GROQ_API_KEY environment variable (see .env.example).
    - Never commit real API keys to GitHub.

Models used (Groq's lineup changes often — check
https://console.groq.com/docs/models if these ever stop working):
    - Text-only messages:  openai/gpt-oss-120b
    - Messages with a screenshot: qwen/qwen3.6-27b (currently Groq's
      vision-capable model; marked "preview" by Groq, so it may be
      renamed/replaced — swap TEXT_MODEL / VISION_MODEL below if so).
"""

from __future__ import annotations

import base64
import json
import os
import re
from typing import Optional

from dotenv import load_dotenv

# Load variables from a local .env file if present (safe no-op in
# environments like Streamlit Cloud where secrets are injected another way).
load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

TEXT_MODEL = "openai/gpt-oss-120b"
VISION_MODEL = "qwen/qwen3.6-27b"

VALID_RISK_LEVELS = {"Low", "Suspicious", "High"}

# --------------------------------------------------------------------------
# Fallback result — used any time we cannot get a trustworthy answer from
# the AI provider. The app must never crash or silently pretend analysis
# succeeded.
# --------------------------------------------------------------------------
FALLBACK_RESULT: dict = {
    "risk_level": "Suspicious",
    "risk_score": 50,
    "scam_type": "Unable to analyze",
    "red_flags": ["AI analysis could not be completed"],
    "explanation": "The message could not be fully analyzed.",
    "recommended_action": (
        "Do not click links or share OTP, PIN, CNIC, or bank details "
        "until the message is verified."
    ),
    "roman_urdu_advice": (
        "Is message par foran bharosa na karein. Link par click ya OTP, "
        "PIN aur bank details share na karein."
    ),
}


# --------------------------------------------------------------------------
# Client setup
# --------------------------------------------------------------------------
def _get_client():
    """
    Build and return a Groq API client.

    Returns None if no API key is configured, so callers can fall back
    cleanly instead of raising.
    """
    if not GROQ_API_KEY:
        return None

    # Imported lazily so the rest of the app can still run / be imported
    # even if the dependency is missing for some reason.
    from groq import Groq

    return Groq(api_key=GROQ_API_KEY)


# --------------------------------------------------------------------------
# Prompt
# --------------------------------------------------------------------------
def _build_prompt(message_text: str, has_image: bool) -> str:
    """Build the scam-detection instruction prompt sent to the model."""
    text_part = message_text.strip() if message_text else ""

    image_instruction = (
        "An image (screenshot) is attached. First read/extract any visible "
        "text from the screenshot (SMS, WhatsApp, banking app, etc.), then "
        "analyze that extracted content the same way you would analyze "
        "pasted text. If both a text message and a screenshot are provided, "
        "analyze them together as one message."
        if has_image
        else "No screenshot was provided. Analyze only the text message below."
    )

    return f"""You are ScamShield PK, a strict scam-message classifier for
Pakistani users. You are NOT a general chatbot — only classify scam risk.

Messages may be in English, Roman Urdu, or a mix of both. Common scam
patterns to look for include (but are not limited to):
- Urgency or threats ("turant", "account block ho jayega", act now)
- Fake bank / mobile wallet alerts (JazzCash, Easypaisa, bank impersonation)
- Fake government benefit messages (e.g. BISP, Ehsaas)
- Lottery / prize / lucky draw scams
- Job offers or advance-fee requests (visa fee, processing fee)
- Suspicious or shortened links (bit.ly, tinyurl, unofficial domains)
- Requests for OTP, PIN, CNIC, or bank/account details
- Suspicious personal phone numbers posing as official helplines
- Impersonation of companies, banks, or government bodies

{image_instruction}

Guidelines:
- Do not assume every message is a scam. Many everyday messages are safe.
- Do not classify something as High risk just because it mentions money.
- Consider context, urgency, impersonation, links, advance-fee requests,
  and requests for sensitive information.
- Do not invent facts that are not present in the message.
- If the evidence is weak or ambiguous, choose "Low" or "Suspicious"
  rather than "High".
- Scoring guide: 0-30 = Low, 31-69 = Suspicious, 70-100 = High. Use this
  as guidance, but base the final score on the actual evidence.

Respond with ONLY a single valid JSON object. No Markdown, no ```json
fences, no commentary before or after it. The JSON object must have
EXACTLY these keys:

{{
  "risk_level": "Low" | "Suspicious" | "High",
  "risk_score": <integer 0-100>,
  "scam_type": "<short label, e.g. 'Fake bank alert', 'None detected'>",
  "red_flags": ["<short reason 1>", "<short reason 2>", ...],
  "explanation": "<1-2 sentence explanation in English>",
  "recommended_action": "<short safe action for the user, in English>",
  "roman_urdu_advice": "<short simple advice written in Roman Urdu>"
}}

If no scam indicators are found, return risk_level "Low", a low
risk_score, and an empty red_flags list.

Message text to analyze:
\"\"\"{text_part if text_part else "(no text provided, see image)"}\"\"\"
"""


# --------------------------------------------------------------------------
# Response parsing
# --------------------------------------------------------------------------
def _parse_json_response(raw_text: str) -> Optional[dict]:
    """
    Safely extract a JSON object from the model's raw text response.

    Handles: plain JSON, JSON wrapped in ```json ... ``` fences, extra
    whitespace/prose around the object, and returns None (never raises)
    if nothing usable is found.
    """
    if not raw_text:
        return None

    cleaned = raw_text.strip()

    # Strip ```json ... ``` or ``` ... ``` fences if present.
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    # Try direct parse first.
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass

    # Fallback: grab the first {...} block in case of stray extra text.
    brace_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if brace_match:
        try:
            parsed = json.loads(brace_match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass

    return None


def _normalize_result(data: dict) -> dict:
    """
    Fill in any missing fields and coerce types so the returned dict
    always matches the agreed schema exactly, regardless of what the
    model actually returned.
    """
    result = dict(FALLBACK_RESULT)  # start from safe defaults
    result.update({k: v for k, v in data.items() if k in FALLBACK_RESULT})

    # risk_level must be one of the three allowed values.
    risk_level = result.get("risk_level")
    if risk_level not in VALID_RISK_LEVELS:
        result["risk_level"] = "Suspicious"

    # risk_score must be an int between 0 and 100.
    try:
        score = int(round(float(result.get("risk_score", 50))))
    except (TypeError, ValueError):
        score = 50
    result["risk_score"] = max(0, min(100, score))

    # red_flags must always be a list of strings.
    flags = result.get("red_flags")
    if not isinstance(flags, list):
        flags = [str(flags)] if flags else []
    result["red_flags"] = [str(f) for f in flags]

    # Remaining text fields must always be strings.
    for key in ("scam_type", "explanation", "recommended_action", "roman_urdu_advice"):
        if not isinstance(result.get(key), str) or not result.get(key):
            result[key] = FALLBACK_RESULT[key]

    return result


def _fallback_result(reason: str = "") -> dict:
    """
    Return a safe fallback result. `reason` is for internal debugging only
    (e.g. could be logged server-side) and is never included in the
    returned dict, so the API key or error internals are never leaked
    to the user.
    """
    return dict(FALLBACK_RESULT)


def _image_to_data_url(image_bytes: bytes) -> str:
    """Convert raw image bytes into a base64 data: URL for the vision model."""
    mime_type = "image/jpeg" if image_bytes[:3] == b"\xff\xd8\xff" else "image/png"
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
def analyze_message(text: str, image_bytes: bytes | None = None) -> dict:
    """
    Analyze a message (and optionally a screenshot) for scam indicators
    using the Groq API.

    Args:
        text: The message text pasted by the user. May be empty if only
            a screenshot was provided.
        image_bytes: Optional raw bytes of an uploaded screenshot image
            (PNG/JPEG) for vision analysis.

    Returns:
        dict matching the team's agreed JSON contract (see module
        docstring). This function never raises — any failure results in
        FALLBACK_RESULT (or a normalized best-effort result).
    """
    message_text = text or ""

    if not message_text.strip() and not image_bytes:
        # Nothing to analyze — not an API failure, just no input.
        return _normalize_result(
            {
                "risk_level": "Low",
                "risk_score": 0,
                "scam_type": "None detected",
                "red_flags": [],
                "explanation": "No message text or screenshot was provided.",
                "recommended_action": "Paste a message or upload a screenshot to check.",
                "roman_urdu_advice": "Check karne ke liye pehle message paste karein ya screenshot upload karein.",
            }
        )

    client = _get_client()
    if client is None:
        return _fallback_result("missing_api_key")

    try:
        prompt = _build_prompt(message_text, has_image=bool(image_bytes))

        if image_bytes:
            user_content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": _image_to_data_url(image_bytes)}},
            ]
            model = VISION_MODEL
        else:
            user_content = prompt
            model = TEXT_MODEL

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": user_content}],
            temperature=0.2,
        )

        raw_text = response.choices[0].message.content if response.choices else None
        parsed = _parse_json_response(raw_text) if raw_text else None

        if parsed is None:
            return _fallback_result("unparseable_response")

        return _normalize_result(parsed)

    except Exception:
        # Covers invalid API key, network errors, quota errors, unexpected
        # SDK exceptions, etc. Never leak exception details (which could
        # theoretically include request info) back to the UI.
        return _fallback_result("api_exception")