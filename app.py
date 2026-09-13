"""
ScamShield PK - app.py (INTEGRATED VERSION - Person 4)
--------------------------------------------------------
This file keeps Person 1's original screens (Login, Welcome, Dashboard)
but replaces the old DUMMY functions with the team's REAL, already-written
integration code:

    Person 2 -> utils/gemini.py         -> analyze_message(text, image_bytes)
    Person 3 -> virustotal/virus.py      -> check_message_links(message_text)
    Person 3 -> virustotal/riskengine.py -> combine_risk_score(gemini_result, vt_results)
                                          -> verify_contact(number)

Nothing in utils/gemini.py, virustotal/virus.py, or virustotal/riskengine.py
needs to change - this file only IMPORTS and CALLS their existing functions.
"""

import streamlit as st

from utils.gemini import analyze_message
from virustotal.virus import check_message_links
from virustotal.riskengine import combine_risk_score, verify_contact

# ---------------------------------------------------------
# PAGE SETTINGS
# ---------------------------------------------------------
st.set_page_config(page_title="ScamShield PK", page_icon="🛡️", layout="centered")

# ---------------------------------------------------------
# SESSION STATE (Streamlit mein data yaad rakhne ka tareeqa)
# ---------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "login"        # login -> welcome -> dashboard
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "history" not in st.session_state:
    st.session_state.history = []          # Recent Checks yahan store hongi


# ---------------------------------------------------------
# REAL INTEGRATION LOGIC (replaces the old dummy functions)
# ---------------------------------------------------------
def get_ai_result(message_text: str, image_bytes: bytes | None = None) -> dict:
    """
    Real pipeline:
    1. Person 2's Groq/Gemini model reads the message (+ screenshot) and
       returns risk_level, risk_score, red_flags, etc.
    2. Person 3's VirusTotal check looks at any links inside the message.
    3. Person 3's combine_risk_score() merges both into the final result
       shown to the user.

    This function never raises - any failure inside the real modules
    already falls back safely (see their own docstrings), and we wrap
    the whole pipeline in a try/except as a last line of defense so the
    UI never crashes.
    """
    try:
        gemini_result = analyze_message(message_text, image_bytes=image_bytes)
    except Exception:
        gemini_result = {
            "risk_score": 50,
            "scam_type": "Unable to analyze",
            "red_flags": ["AI analysis could not be completed"],
            "explanation": "The message could not be fully analyzed.",
            "recommended_action": "Do not click links or share OTP/PIN until verified.",
            "roman_urdu_advice": "Is message par foran bharosa na karein.",
        }

    vt_results = []
    if message_text and message_text.strip():
        try:
            # Only check the first 2 links to keep the wait time reasonable -
            # each VirusTotal check can take ~15 seconds.
            all_vt_results = check_message_links(message_text)
            vt_results = all_vt_results[:2]
        except Exception:
            vt_results = []

    try:
        final_result = combine_risk_score(gemini_result, vt_results)
    except Exception:
        final_result = gemini_result
        final_result.setdefault("risk_level", "Suspicious")

    return final_result


# ---------------------------------------------------------
# SCREEN 1: LOGIN
# ---------------------------------------------------------
def login_screen():
    st.markdown("## 🛡️ ScamShield PK")
    st.markdown("### Welcome")
    st.caption("Login to continue")

    name = st.text_input("Your Name", placeholder="e.g. Ali Khan")
    email = st.text_input("Email (optional)", placeholder="you@example.com")

    if st.button("Login", type="primary", use_container_width=True):
        if name.strip() == "":
            st.warning("Pehle apna naam likhein.")
        else:
            st.session_state.user_name = name.strip()
            st.session_state.page = "welcome"
            st.rerun()


# ---------------------------------------------------------
# SCREEN 2: WELCOME
# ---------------------------------------------------------
def welcome_screen():
    st.markdown("## 🛡️ ScamShield PK")
    st.markdown(f"### Welcome, {st.session_state.user_name}!")
    st.write(
        "ScamShield PK aapko fake SMS, WhatsApp aur bank scams "
        "pehchanne mein madad karta hai."
    )
    st.markdown("- ✓ Message ya screenshot check karein")
    st.markdown("- ✓ Risk score aur red flags dekhein")
    st.markdown("- ✓ Roman Urdu mein simple advice payein")

    if st.button("Shuru Karein →", type="primary", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()


# ---------------------------------------------------------
# SCREEN 3: MAIN DASHBOARD
# ---------------------------------------------------------
def dashboard_screen():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("## ScamShield PK - Dashboard")
    with col2:
        st.markdown(f"**{st.session_state.user_name}**")

    st.markdown("---")

    # ---- Check a Message ----
    st.subheader("Check a Message")
    message_text = st.text_area(
        "Message paste karein",
        placeholder="JazzCash Alert: PKR 25,000 received. Stop transaction call 0300-XXXXXXX",
        label_visibility="collapsed",
        height=100,
    )
    uploaded_image = st.file_uploader("Ya screenshot upload karein", type=["png", "jpg", "jpeg"])

    if st.button("Check Now", type="primary"):
        if message_text.strip() == "" and uploaded_image is None:
            st.warning("Pehle message likhein ya screenshot upload karein.")
        else:
            image_bytes = uploaded_image.getvalue() if uploaded_image else None
            with st.spinner("AI aur VirusTotal check ho raha hai... (link hone par 15-30 second lag sakte hain)"):
                result = get_ai_result(message_text, image_bytes=image_bytes)

            st.session_state.last_result = result
            short_text = message_text[:35] + "..." if message_text else "Screenshot check"
            st.session_state.history.insert(0, {"text": short_text, "risk": result["risk_level"]})

    # ---- Result ----
    if "last_result" in st.session_state:
        r = st.session_state.last_result
        st.markdown("### Result")

        color = {"High": "🔴", "Suspicious": "🟠", "Low": "🟢"}.get(r["risk_level"], "⚪")
        st.markdown(f"**{color} {r['risk_score']}% {r['risk_level']} Risk**")

        if r.get("red_flags"):
            st.markdown("**Red Flags:**")
            for flag in r["red_flags"]:
                st.markdown(f"- {flag}")

        st.info(f"Advice: {r.get('roman_urdu_advice', '')}")

        with st.expander("More details"):
            st.write(f"**Scam type:** {r.get('scam_type', 'N/A')}")
            st.write(f"**Explanation:** {r.get('explanation', 'N/A')}")
            st.write(f"**Recommended action:** {r.get('recommended_action', 'N/A')}")

    st.markdown("---")

    # ---- History ----
    st.subheader("Recent Checks (History)")
    if st.session_state.history:
        for item in st.session_state.history[:5]:
            risk_color = {"High": "red", "Suspicious": "orange", "Low": "green"}.get(item["risk"], "gray")
            st.markdown(f"- {item['text']}  :{risk_color}[**{item['risk']} Risk**]")
    else:
        st.caption("Abhi tak koi check nahi kiya gaya.")

    st.markdown("---")

    col_a, col_b = st.columns(2)

    # ---- Trending Scams ----
    with col_a:
        st.subheader("Trending Scams")
        st.markdown("1. Fake BISP registration link")
        st.markdown("2. 'Jeeto Pakistan' lottery SMS")
        st.markdown("3. Fake bank block alerts")

    # ---- Verify a Contact ----
    with col_b:
        st.subheader("Verify a Contact")
        number = st.text_input("Number", placeholder="0300-1234567", label_visibility="collapsed")
        if st.button("Verify"):
            if number.strip():
                try:
                    contact_result = verify_contact(number.strip())
                    status = contact_result.get("status", "invalid_format")
                    message = contact_result.get("message", "Format samajh nahi aaya.")
                    if status == "official_pattern":
                        st.success(message)
                    elif status == "suspicious_personal_number":
                        st.warning(message)
                    else:
                        st.info(message)
                except Exception:
                    st.error("Number verify karte waqt masla hua, dobara koshish karein.")
            else:
                st.warning("Number likhein pehle.")


# ---------------------------------------------------------
# MAIN ROUTER (kaunsa screen dikhana hai)
# ---------------------------------------------------------
if st.session_state.page == "login":
    login_screen()
elif st.session_state.page == "welcome":
    welcome_screen()
elif st.session_state.page == "dashboard":
    dashboard_screen()
