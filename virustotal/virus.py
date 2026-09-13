"""
utils/virustotal.py
Person 3's job: check if a link inside a message is malicious, using VirusTotal API v3.

Setup:
1. Go to virustotal.com -> make a free account
2. Profile icon (top right) -> "API Key" -> copy it
3. Put it in a .env file in the project root as:
       VIRUSTOTAL_API_KEY=your_key_here
4. Never commit .env to GitHub (add it to .gitignore)

Free tier limits: 4 requests/min, 500/day - so don't hammer it in a loop.
"""

import os
import re
import time
import base64
import requests

VT_BASE_URL = "https://www.virustotal.com/api/v3"
VT_API_KEY = os.environ.get("VIRUSTOTAL_API_KEY", "")


# ---------------------------------------------------------------------------
# 1. Extract URLs from a message using regex
# ---------------------------------------------------------------------------
URL_REGEX = re.compile(
    r"(https?://[^\s]+)|(www\.[^\s]+)|([a-zA-Z0-9-]+\.(?:com|pk|net|org|info|xyz|link|club)[^\s]*)",
    re.IGNORECASE,
)


def extract_urls(text: str) -> list:
    """
    Pulls any link-looking substrings out of a message.
    Example: "Aap ka account block, yahan click karein bit.ly/xyz123"
             -> ["bit.ly/xyz123"]
    """
    if not text:
        return []

    matches = URL_REGEX.findall(text)
    urls = []
    for group in matches:
        # findall with multiple groups returns tuples; pick whichever matched
        candidate = next((g for g in group if g), None)
        if candidate:
            # strip trailing punctuation that often gets stuck to links in SMS
            candidate = candidate.strip().rstrip(".,)!?\"'")
            urls.append(candidate)

    # de-duplicate while keeping order
    seen = set()
    unique_urls = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)
    return unique_urls


def _normalize_url(url: str) -> str:
    """VirusTotal wants a proper URL with a scheme."""
    if not url.startswith(("http://", "https://")):
        return "http://" + url
    return url


# ---------------------------------------------------------------------------
# 2. Submit a URL to VirusTotal and get back the verdict
# ---------------------------------------------------------------------------
def check_url_virustotal(url: str, wait_seconds: int = 15) -> dict:
    """
    Submits a URL for scanning and polls once for the result.

    Returns a dict like:
    {
        "url": "...",
        "checked": True/False,   # False if API failed / no key / rate limited
        "malicious": 0,
        "suspicious": 0,
        "harmless": 0,
        "verdict": "malicious" | "suspicious" | "clean" | "unknown",
        "error": None or "reason"
    }

    Design note: this NEVER raises. If VirusTotal is down, rate-limited, or
    the key is missing, it returns checked=False with an error message so the
    rest of the app (and Person 1's UI) doesn't crash.
    """
    result = {
        "url": url,
        "checked": False,
        "malicious": 0,
        "suspicious": 0,
        "harmless": 0,
        "verdict": "unknown",
        "error": None,
    }

    if not VT_API_KEY:
        result["error"] = "VIRUSTOTAL_API_KEY not set"
        return result

    normalized = _normalize_url(url)
    headers = {"x-apikey": VT_API_KEY}

    try:
        # Step 1: submit the URL for analysis
        submit_resp = requests.post(
            f"{VT_BASE_URL}/urls",
            headers=headers,
            data={"url": normalized},
            timeout=15,
        )

        if submit_resp.status_code == 429:
            result["error"] = "rate_limited"
            return result
        submit_resp.raise_for_status()

        analysis_id = submit_resp.json()["data"]["id"]

        # Step 2: wait a bit for the scan to finish, then fetch results
        time.sleep(wait_seconds)

        analysis_resp = requests.get(
            f"{VT_BASE_URL}/analyses/{analysis_id}",
            headers=headers,
            timeout=15,
        )
        analysis_resp.raise_for_status()
        stats = analysis_resp.json()["data"]["attributes"]["stats"]

        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
        harmless = stats.get("harmless", 0)

        if malicious > 0:
            verdict = "malicious"
        elif suspicious > 0:
            verdict = "suspicious"
        else:
            verdict = "clean"

        result.update(
            {
                "checked": True,
                "malicious": malicious,
                "suspicious": suspicious,
                "harmless": harmless,
                "verdict": verdict,
            }
        )
        return result

    except requests.exceptions.RequestException as e:
        result["error"] = f"network_error: {e}"
        return result
    except (KeyError, ValueError) as e:
        result["error"] = f"bad_response: {e}"
        return result


def check_message_links(message_text: str) -> list:
    """
    Convenience wrapper: extract every URL in a message and check all of them.
    Returns a list of check_url_virustotal() results (empty list if no links found).
    """
    urls = extract_urls(message_text)
    return [check_url_virustotal(u) for u in urls]


# Quick manual test - only runs if you execute this file directly
if __name__ == "__main__":
    sample = "JazzCash Alert: PKR 25,000 received. Stop transaction call 0300-XXXXXXX visit http://bit.ly/fake-jazzcash"
    print("Found URLs:", extract_urls(sample))
    print(check_message_links(sample))  # uncomment once your API key is set
