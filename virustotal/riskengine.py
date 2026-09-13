"""
utils/risk_engine.py
Person 3's job (part 2): combine Person 2's Gemini result with the VirusTotal
link check into ONE final result, in the JSON format the whole team agreed on:

{
  "risk_level": "Low" | "Suspicious" | "High",
  "risk_score": 0-100,
  "scam_type": "...",
  "red_flags": ["...", "..."],
  "explanation": "...",
  "recommended_action": "...",
  "roman_urdu_advice": "..."
}

This file does NOT call Gemini itself - it expects Person 2's JSON as input.
"""

import re

# A few known official short/help-line numbers for common PK services.
# (Demo-purposes list - extend this as you find more real ones.)
KNOWN_OFFICIAL_NUMBERS = {
    "jazzcash": ["786", "4456"],
    "easypaisa": ["3737", "2233"],
    "bank_generic_helpline_prefixes": ["111"],  # most PK banks use 111-XXX-XXX UAN format
}

# A normal Pakistani mobile number: 03XXXXXXXXX (11 digits) or +923XXXXXXXXX
MOBILE_NUMBER_REGEX = re.compile(r"^(\+92|0)?3\d{9}$")
UAN_REGEX = re.compile(r"^111-?\d{3}-?\d{3}$")  # bank helpline style: 111-234-567


# ---------------------------------------------------------------------------
# 1. Verify a Contact number
# ---------------------------------------------------------------------------
def verify_contact(number: str) -> dict:
    """
    Simple heuristic check: does this number look like an official
    company/bank line, or a random personal mobile number?

    Scammers almost always ask you to call/WhatsApp a personal mobile number
    pretending it's "official support" - that's the #1 red flag.

    Returns:
    {
        "number": "...",
        "status": "official_pattern" | "suspicious_personal_number" | "invalid_format",
        "message": "human readable Roman Urdu note"
    }
    """
    cleaned = re.sub(r"[\s\-]", "", number.strip())

    if UAN_REGEX.match(number.strip()):
        return {
            "number": number,
            "status": "official_pattern",
            "message": "Ye official bank helpline (UAN) jaisa number hai.",
        }

    for short_code in KNOWN_OFFICIAL_NUMBERS["jazzcash"] + KNOWN_OFFICIAL_NUMBERS["easypaisa"]:
        if cleaned == short_code:
            return {
                "number": number,
                "status": "official_pattern",
                "message": "Ye known official short-code hai.",
            }

    if MOBILE_NUMBER_REGEX.match(cleaned):
        # Looks like a normal personal mobile number, not a company line
        return {
            "number": number,
            "status": "suspicious_personal_number",
            "message": (
                "⚠ Ye ek personal mobile number lagta hai. Asli banks/JazzCash/Easypaisa "
                "kabhi personal number se call/WhatsApp nahi karte - sirf official "
                "helpline (jaise 111-XXX-XXX) ya app ke through contact karte hain."
            ),
        }

    return {
        "number": number,
        "status": "invalid_format",
        "message": "Number ka format samajh nahi aaya, dobara check karein.",
    }


# ---------------------------------------------------------------------------
# 2. Combine Gemini's result + VirusTotal's result into the final JSON
# ---------------------------------------------------------------------------
def combine_risk_score(gemini_result: dict, vt_results: list) -> dict:
    """
    gemini_result: the JSON dict Person 2's function returns, expected to
                   already roughly follow the team schema, e.g.:
                   {
                     "risk_score": 70,
                     "scam_type": "...",
                     "red_flags": [...],
                     "explanation": "...",
                     "recommended_action": "...",
                     "roman_urdu_advice": "..."
                   }

    vt_results: list of dicts from virustotal.check_url_virustotal(), one per
                link found in the message (can be an empty list if no links).

    Returns the final combined dict, matching the team's agreed schema.
    """
    # Start from Gemini's numbers, with safe fallbacks in case something's missing
    base_score = gemini_result.get("risk_score", 0)
    red_flags = list(gemini_result.get("red_flags", []))
    scam_type = gemini_result.get("scam_type", "Unknown")
    explanation = gemini_result.get("explanation", "")
    roman_urdu_advice = gemini_result.get("roman_urdu_advice", "")
    recommended_action = gemini_result.get("recommended_action", "")

    # Fold in VirusTotal's verdict on any links found
    link_bonus = 0
    for vt in vt_results:
        if not vt.get("checked"):
            continue  # VT failed/unavailable - just skip it, don't crash
        if vt["verdict"] == "malicious":
            link_bonus = max(link_bonus, 40)
            red_flags.append(f"Link '{vt['url']}' VirusTotal par malicious nikla")
        elif vt["verdict"] == "suspicious":
            link_bonus = max(link_bonus, 20)
            red_flags.append(f"Link '{vt['url']}' VirusTotal par suspicious nikla")

    final_score = min(100, base_score + link_bonus)

    if final_score >= 70:
        risk_level = "High"
    elif final_score >= 35:
        risk_level = "Suspicious"
    else:
        risk_level = "Low"

    return {
        "risk_level": risk_level,
        "risk_score": final_score,
        "scam_type": scam_type,
        "red_flags": red_flags,
        "explanation": explanation,
        "recommended_action": recommended_action or (
            "Is number/link par click na karein, na hi OTP share karein."
            if risk_level != "Low"
            else "Message theek lagta hai, phir bhi hamesha ehtiyaat karein."
        ),
        "roman_urdu_advice": roman_urdu_advice,
    }


# Quick manual test
if __name__ == "__main__":
    fake_gemini_output = {
        "risk_score": 60,
        "scam_type": "Fake bank alert",
        "red_flags": ["Urgency: 'stop transaction, call now'"],
        "explanation": "Message pressures the user to act immediately.",
        "recommended_action": "",
        "roman_urdu_advice": "Kisi ko OTP na dein.",
    }
    fake_vt_output = [
        {"url": "bit.ly/fake-jazzcash", "checked": True, "verdict": "malicious",
         "malicious": 12, "suspicious": 2, "harmless": 50, "error": None}
    ]

    print(combine_risk_score(fake_gemini_output, fake_vt_output))
    print(verify_contact("0300-1234567"))
    print(verify_contact("111-234-567"))
