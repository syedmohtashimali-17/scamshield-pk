"""
utils/risk_engine.py
---------------------
OWNER: Person 3 (VirusTotal + Risk Score + Contact Verify)

PLACEHOLDER / MOCK implementation. Person 3 should implement the real
VirusTotal checks in a sibling module (utils/virustotal.py) and wire the
real logic into compute_final_risk() and verify_contact() below, while
keeping the same function names, inputs, and output shapes so app.py
does not need to change.
"""

import os
import re

VIRUSTOTAL_API_KEY = os.environ.get("VIRUSTOTAL_API_KEY")

URL_REGEX = re.compile(r"(https?://[^\s]+|www\.[^\s]+|bit\.ly/[^\s]+)")

# Pakistani mobile prefixes considered "official-looking" for demo purposes.
# Person 3: replace with real carrier/official-number validation logic.
OFFICIAL_NUMBER_PATTERN = re.compile(r"^0(2\d{2}|21|42|51)-?\d{7,8}$")  # landline/official style
PERSONAL_MOBILE_PATTERN = re.compile(r"^03\d{2}-?\d{7}$")


def extract_urls(text: str) -> list[str]:
    """Extract candidate URLs from a message using regex."""
    return URL_REGEX.findall(text or "")


def check_url_with_virustotal(url: str) -> dict:
    """
    Check a single URL against VirusTotal.

    TODO (Person 3): Replace this mock with a real VirusTotal API call:
      1. POST the URL to https://www.virustotal.com/api/v3/urls
      2. GET the analysis report using the returned id
      3. Return malicious/harmless vote counts

    Returns a dict like:
        {"url": str, "malicious": bool, "detail": str}
    """
    if not VIRUSTOTAL_API_KEY:
        return {"url": url, "malicious": None, "detail": "VirusTotal API key not configured."}

    try:
        # TODO: real VirusTotal request goes here.
        # Mock: treat shortened links as suspicious for demo purposes.
        is_shortened = "bit.ly" in url or "tinyurl" in url
        return {
            "url": url,
            "malicious": is_shortened,
            "detail": "Shortened link (mock flagged as suspicious)" if is_shortened else "No issues found (mock).",
        }
    except Exception:
        return {"url": url, "malicious": None, "detail": "VirusTotal check failed, treated as inconclusive."}


def compute_final_risk(gemini_result: dict, message_text: str) -> dict:
    """
    Combine Person 2's Gemini result with VirusTotal URL findings to
    produce the final result shown to the user.

    Args:
        gemini_result: dict returned by utils.gemini.analyze_message()
        message_text: original message text (used to extract URLs)

    Returns:
        dict with the same shape as gemini_result, but with risk_score
        and red_flags adjusted based on VirusTotal findings.
    """
    result = dict(gemini_result)  # shallow copy so we don't mutate the input
    urls = extract_urls(message_text)
    vt_flags = []

    for url in urls:
        vt_check = check_url_with_virustotal(url)
        if vt_check.get("malicious"):
            vt_flags.append(f"Malicious/suspicious link detected: {vt_check['url']}")
            result["risk_score"] = min(100, result.get("risk_score", 0) + 25)

    if vt_flags:
        result["red_flags"] = result.get("red_flags", []) + vt_flags
        if result["risk_score"] >= 70:
            result["risk_level"] = "High"
        elif result["risk_score"] >= 40:
            result["risk_level"] = "Suspicious"

    return result


def verify_contact(phone_number: str) -> dict:
    """
    Simple check on whether a phone number looks like an official
    business/helpline number vs. a personal mobile number.

    TODO (Person 3): Improve this with a real pattern list of known
    official helplines (banks, telecom, government) if time allows.
    """
    cleaned = phone_number.strip().replace(" ", "")

    if OFFICIAL_NUMBER_PATTERN.match(cleaned):
        return {"number": cleaned, "status": "official_pattern", "message": "Looks like an official landline/helpline pattern."}
    elif PERSONAL_MOBILE_PATTERN.match(cleaned):
        return {"number": cleaned, "status": "suspicious", "message": "This looks like a personal mobile number, not an official helpline."}
    else:
        return {"number": cleaned, "status": "unknown", "message": "Could not confidently classify this number."}
