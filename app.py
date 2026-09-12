"""
ScamShield PK — Main Streamlit App
====================================
OWNER (integration): Person 4
Depends on:
    - utils/gemini.py        (Person 2 — AI message/screenshot analysis)
    - utils/risk_engine.py   (Person 3 — VirusTotal + final risk scoring + contact verify)

This file wires together:
    - Login / Welcome screens   (Person 1's UI, structure preserved here)
    - Main dashboard: message checker + result display
    - Session-based History (st.session_state, no database)
    - Trending Scams cards loaded from data/scams.json
    - Verify a Contact widget
"""

import json
import os
from datetime import datetime

import streamlit as st

from utils import gemini
from utils import risk_engine

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------
SCAMS_JSON_PATH = os.path.join(os.path.dirname(__file__), "data", "scams.json")

st.set_page_config(
    page_title="ScamShield PK",
    page_icon="🛡️",
    layout="centered",
)

RISK_COLORS = {
    "Low": "#1a7f37",
    "Suspicious": "#b8860b",
    "High": "#d1242f",
}


# --------------------------------------------------------------------------
# SESSION STATE
# --------------------------------------------------------------------------
def init_session_state() -> None:
    """Initialize all session_state keys used across the app, exactly once."""
    defaults = {
        "logged_in": False,
        "user_name": "",
        "user_email": "",
        "page": "login",       # login -> welcome -> dashboard
        "history": [],          # list of dicts: {timestamp, message, result}
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def add_to_history(message_text: str, result: dict) -> None:
    """Append a new checked message + its result to the session history."""
    st.session_state.history.insert(0, {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "message": message_text[:80] + ("..." if len(message_text) > 80 else ""),
        "risk_level": result.get("risk_level", "Unknown"),
        "risk_score": result.get("risk_score", 0),
    })
    # Keep history from growing unbounded during a long demo session
    st.session_state.history = st.session_state.history[:20]


# --------------------------------------------------------------------------
# DATA LOADING
# --------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_trending_scams() -> list[dict]:
    """Load trending scam examples from data/scams.json. Fails gracefully."""
    try:
        with open(SCAMS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("scams", [])
    except (FileNotFoundError, json.JSONDecodeError):
        st.warning("Trending scams data could not be loaded.")
        return []


# --------------------------------------------------------------------------
# SCREENS
# --------------------------------------------------------------------------
def render_login_page() -> None:
    st.markdown("## 🛡️ ScamShield PK")
    st.markdown("### Welcome")
    st.caption("Login to continue")

    with st.form("login_form"):
        name = st.text_input("Your Name", placeholder="e.g. Ali Khan")
        email = st.text_input("Email (optional)", placeholder="you@example.com")
        submitted = st.form_submit_button("Login", use_container_width=True)

    st.caption("(No password / real account needed - demo login)")

    if submitted:
        if not name.strip():
            st.error("Apna naam likhna zaroori hai.")
        else:
            st.session_state.user_name = name.strip()
            st.session_state.user_email = email.strip()
            st.session_state.logged_in = True
            st.session_state.page = "welcome"
            st.rerun()


def render_welcome_page() -> None:
    st.markdown("## 🛡️ ScamShield PK")
    st.markdown(f"### Welcome, {st.session_state.user_name}!")
    st.write(
        "ScamShield PK aapko fake SMS, WhatsApp aur bank scams "
        "pehchanne mein madad karta hai."
    )
    st.markdown(
        "- ✓ Message ya screenshot check karein\n"
        "- ✓ Risk score aur red flags dekhein\n"
        "- ✓ Roman Urdu mein simple advice payein"
    )
    if st.button("Shuru Karein →", type="primary", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()


def render_result(result: dict) -> None:
    """Render the risk result card: score badge, red flags, advice."""
    color = RISK_COLORS.get(result.get("risk_level"), "#666666")
    st.markdown("#### Result")
    st.markdown(
        f"""
        <div style="background-color:{color}; color:white; padding:10px 16px;
                    border-radius:8px; font-weight:bold; display:inline-block;">
            {result.get('risk_score', 0)}% {result.get('risk_level', 'Unknown')} Risk
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**Red Flags:**")
    flags = result.get("red_flags", [])
    if flags:
        for flag in flags:
            st.markdown(f"- {flag}")
    else:
        st.markdown("- Koi red flag detect nahi hua")

    st.info(f"**Advice:** {result.get('roman_urdu_advice', '')}")

    with st.expander("More details"):
        st.write(f"**Scam type:** {result.get('scam_type', 'N/A')}")
        st.write(f"**Explanation:** {result.get('explanation', 'N/A')}")
        st.write(f"**Recommended action:** {result.get('recommended_action', 'N/A')}")


def render_message_checker() -> None:
    """Main feature: text/screenshot input -> Gemini -> Risk Engine -> result."""
    st.markdown("#### Check a Message")

    message_text = st.text_area(
        "Suspicious message",
        placeholder="JazzCash Alert: PKR 25,000 received. Stop transaction call 0300-XXXXXXX",
        label_visibility="collapsed",
        height=90,
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        screenshot = st.file_uploader(
            "Upload Screenshot", type=["png", "jpg", "jpeg"], label_visibility="collapsed"
        )
    with col2:
        check_clicked = st.button("Check Now", type="primary", use_container_width=True)

    if check_clicked:
        if not message_text.strip() and not screenshot:
            st.error("Message paste karein ya screenshot upload karein.")
            return

        image_bytes = screenshot.getvalue() if screenshot else None

        with st.spinner("Message check ho raha hai..."):
            try:
                gemini_result = gemini.analyze_message(message_text, image_bytes=image_bytes)
                final_result = risk_engine.compute_final_risk(gemini_result, message_text)
            except Exception as e:
                st.error(f"Kuch masla ho gaya, dobara koshish karein. ({e})")
                return

        add_to_history(message_text or "[Screenshot only]", final_result)
        render_result(final_result)


def render_history_sidebar() -> None:
    """Sleek sidebar showing recent checks from this browser session only."""
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user_name or 'Guest'}")
        st.caption(st.session_state.user_email or "No email provided")
        st.divider()

        st.markdown("### 🕘 Recent Checks")
        if not st.session_state.history:
            st.caption("Abhi tak koi message check nahi kiya gaya.")
        else:
            for item in st.session_state.history:
                color = RISK_COLORS.get(item["risk_level"], "#666666")
                with st.container(border=True):
                    st.markdown(f"**{item['timestamp']}**")
                    st.caption(item["message"])
                    st.markdown(
                        f"<span style='color:{color}; font-weight:bold;'>"
                        f"{item['risk_level']} · {item['risk_score']}%</span>",
                        unsafe_allow_html=True,
                    )

            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.history = []
                st.rerun()

        st.divider()
        st.caption("History sirf is session ke liye hai — refresh/logout se gayab ho jati hai.")


def render_trending_scams() -> None:
    st.markdown("#### Trending Scams")
    scams = load_trending_scams()
    if not scams:
        st.caption("Trending scams abhi load nahi ho sake.")
        return

    for scam in scams:
        with st.container(border=True):
            st.markdown(f"**{scam.get('icon', '⚠️')} {scam['title']}**")
            st.caption(scam.get("category", ""))
            st.write(scam.get("roman_urdu_advice", ""))


def render_verify_contact() -> None:
    st.markdown("#### Verify a Contact")
    number = st.text_input("Phone number", placeholder="0300-1234567", label_visibility="collapsed")
    if st.button("Verify Number"):
        if not number.strip():
            st.error("Number likhein pehle.")
        else:
            result = risk_engine.verify_contact(number.strip())
            if result["status"] == "suspicious":
                st.warning(f"⚠️ {result['message']}")
            elif result["status"] == "official_pattern":
                st.success(f"✅ {result['message']}")
            else:
                st.info(f"ℹ️ {result['message']}")


def render_dashboard() -> None:
    header_col1, header_col2 = st.columns([4, 1])
    with header_col1:
        st.markdown("## 🛡️ ScamShield PK — Dashboard")
    with header_col2:
        st.markdown(f"**{st.session_state.user_name}**")

    st.divider()
    render_message_checker()
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        render_trending_scams()
    with col2:
        render_verify_contact()

    # History lives in the sidebar, not the main flow
    render_history_sidebar()

    with st.sidebar:
        if st.button("🚪 Logout", use_container_width=True):
            for key in ["logged_in", "user_name", "user_email", "page", "history"]:
                st.session_state.pop(key, None)
            st.rerun()


# --------------------------------------------------------------------------
# MAIN ROUTER
# --------------------------------------------------------------------------
def main() -> None:
    init_session_state()

    if not st.session_state.logged_in:
        render_login_page()
    elif st.session_state.page == "welcome":
        render_welcome_page()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()
