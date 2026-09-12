"""
utils/gemini.py
----------------
OWNER: Person 2 (Gemini AI Integration)

This is a PLACEHOLDER / MOCK implementation so that Person 1 and Person 4
can build and test the app UI without waiting for the real Gemini
integration to be finished. Person 2 should replace analyze_message()
with a real call to the Gemini API, but MUST keep the same function
name, input signature, and output JSON shape so nothing else breaks.

Expected output contract (agreed by the whole team):
{
    "risk_level": "Low" | "Suspicious" | "High",
    "risk_score": int (0-100),
    "scam_type": str,
    "red_flags": list[str],
    "explanation": str,
    "recommended_action": str,
    "roman_urdu_advice": str
}
"""

import os
import re
import random

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

FALLBACK_RESULT = {
    "risk_level": "Suspicious",
    "risk_score": 50,
    "scam_type": "Unknown",
    "red_flags": ["AI analysis unavailable, showing fallback result"],
    "explanation": "Gemini API could not be reached or returned an invalid response.",
    "recommended_action": "Manually verify this message before taking any action.",
    "roman_urdu_advice": "Is waqt AI check nahi ho saka. Ehtiyat barten aur khud verify karein.",
}


def analyze_message(text: str, image_bytes: bytes | None = None) -> dict:
    """
    Analyze a message (and optionally a screenshot) for scam indicators.

    Args:
        text: The message text pasted by the user.
        image_bytes: Optional raw bytes of an uploaded screenshot
                      (for Gemini Vision analysis).

    Returns:
        dict matching the team's agreed JSON contract (see module docstring).

    NOTE for Person 2:
        Replace the body of this function with a real Gemini API call
        (google-generativeai SDK). Wrap the API call and JSON parsing in
        try/except so that a malformed response falls back to
        FALLBACK_RESULT instead of crashing the app.
    """
    if not GEMINI_API_KEY:
        return FALLBACK_RESULT

    try:
        # TODO (Person 2): Replace this mock logic with a real Gemini call.
        # Example of what the real implementation should look like:
        #
        # import google.generativeai as genai
        # genai.configure(api_key=GEMINI_API_KEY)
        # model = genai.GenerativeModel("gemini-1.5-flash")
        # prompt = build_scam_detection_prompt(text)
        # response = model.generate_content(prompt)
        # result = safe_json_parse(response.text)
        # return result

        return _mock_analyze(text)

    except Exception:
        return FALLBACK_RESULT


def _mock_analyze(text: str) -> dict:
    """Very simple keyword-based mock so the UI has realistic data to render."""
    text_lower = text.lower()
    urgent_keywords = ["turant", "block", "call now", "call karein", "stop transaction", "jeeta", "lottery", "inaam"]
    has_link = bool(re.search(r"http[s]?://|bit\.ly|www\.", text_lower))
    flags = []

    if any(k in text_lower for k in urgent_keywords):
        flags.append("Urgency language detected ('turant', 'block', 'call now')")
    if has_link:
        flags.append("Message contains a link")
    if re.search(r"\b03\d{2}-?\d{7}\b", text):
        flags.append("Personal mobile number given instead of official helpline")

    if flags:
        score = min(95, 40 + len(flags) * 20)
        return {
            "risk_level": "High" if score >= 70 else "Suspicious",
            "risk_score": score,
            "scam_type": "Fake alert / lottery / bank scam pattern",
            "red_flags": flags,
            "explanation": "Message contains common scam indicators such as urgency or suspicious links.",
            "recommended_action": "Do not click any links or call the number. Verify directly with the official company.",
            "roman_urdu_advice": "Yeh message scam ho sakta hai. Kisi link par click na karein, na hi OTP ya CNIC share karein.",
        }

    return {
        "risk_level": "Low",
        "risk_score": random.randint(5, 20),
        "scam_type": "None detected",
        "red_flags": [],
        "explanation": "No strong scam indicators found in this message.",
        "recommended_action": "Message appears safe, but always stay cautious with personal information.",
        "roman_urdu_advice": "Yeh message theek lagta hai, phir bhi apni personal details kisi ko na dein.",
    }
