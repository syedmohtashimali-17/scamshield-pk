"""
ScamShield PK - Person 1 ka kaam
--------------------------------
Ye file 3 screens banati hai:
1. Login Screen
2. Welcome Screen
3. Main Dashboard (Check + Result + History + Trending Scams + Verify Contact)

Person 2 aur Person 3 apne functions (get_ai_result, check_link) banayenge.
Abhi ke liye maine "DUMMY" (fake/test) functions bana diye hain, taake aap
akele bhi poori UI test kar sakein. Jab Person 2/3 ka kaam ready ho jaye,
bas neeche wale dummy functions ko unke real functions se replace kar dena.
"""

import streamlit as st
import re
import random

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
# DUMMY FUNCTIONS (Person 2 aur 3 inhe real functions se replace karenge)
# ---------------------------------------------------------
def get_ai_result(message_text: str) -> dict:
    """
    NORMALLY ye function Person 2 (Gemini) dega.
    Abhi test ke liye fake result generate kar raha hai,
    lekin EXACT wohi JSON format use kar raha hai jo team ne finalize kiya:
    risk_level, risk_score, scam_type, red_flags, explanation,
    recommended_action, roman_urdu_advice
    """
    text = message_text.lower()
    if any(word in text for word in ["lottery", "jeeti", "click", "block", "otp", "call kare"]):
        return {
            "risk_level": "High",
            "risk_score": random.randint(80, 97),
            "scam_type": "Fake Bank / Lottery Scam",
            "red_flags": [
                "Urgency wali language use ho rahi hai",
                "Personal number diya gaya hai official ki jagah",
                "OTP ya click karne ko bola gaya hai",
            ],
            "explanation": "This message shows common scam patterns like urgency and unofficial contact.",
            "recommended_action": "Is number ko block karein aur kisi ko OTP na dein",
            "roman_urdu_advice": "Yeh fake message lagta hai. Kisi ko OTP ya code kabhi na dein.",
        }
    else:
        return {
            "risk_level": "Low",
            "risk_score": random.randint(5, 20),
            "scam_type": "Normal Message",
            "red_flags": [],
            "explanation": "No obvious scam patterns detected.",
            "recommended_action": "Koi khaas action zaroori nahi",
            "roman_urdu_advice": "Ye message theek lag raha hai, phir bhi hoshiyar rahein.",
        }


def verify_contact(number: str) -> str:
    """
    NORMALLY Person 3 ka function. Abhi simple pattern check kar raha hai:
    official numbers usually 11 digit ya short-code hote hain.
    """
    number = number.strip()
    if re.fullmatch(r"03\d{9}", number):
        return "⚠️ Suspicious - personal number"
    elif re.fullmatch(r"\d{3,5}", number):
        return "✅ Looks like an official short-code"
    else:
        return "❓ Format samajh nahi aaya, dobara check karein"


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
            # Yahan Person 2 ka real function call hoga (text + image)
            result = get_ai_result(message_text)
            st.session_state.last_result = result
            # History mein save karna
            short_text = message_text[:35] + "..." if message_text else "Screenshot check"
            st.session_state.history.insert(0, {"text": short_text, "risk": result["risk_level"]})

    # ---- Result ----
    if "last_result" in st.session_state:
        r = st.session_state.last_result
        st.markdown("### Result")

        color = {"High": "🔴", "Suspicious": "🟠", "Low": "🟢"}.get(r["risk_level"], "⚪")
        st.markdown(f"**{color} {r['risk_score']}% {r['risk_level']} Risk**")

        if r["red_flags"]:
            st.markdown("**Red Flags:**")
            for flag in r["red_flags"]:
                st.markdown(f"- {flag}")

        st.info(f"Advice: {r['roman_urdu_advice']}")

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
                st.warning(verify_contact(number))
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
