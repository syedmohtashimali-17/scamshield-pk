# 🛡️ ScamShield PK

**AI-powered scam message detector built for Pakistan.**

ScamShield PK helps everyday users identify fraudulent SMS, WhatsApp messages, and links — including fake bank alerts, lottery scams, and JazzCash/Easypaisa fraud — using Google's Gemini AI combined with VirusTotal link analysis. Built for a hackathon, with a focus on accessibility for elderly and low-literacy users through simple Roman Urdu explanations.

---

## 📌 Problem

Scammers in Pakistan frequently target users through fake SMS and WhatsApp messages, such as:

- *"Aap ka account block ho gaya hai, is number par call karein"*
- *"Aap ne Jeeto Pakistan lottery jeeti hai"*
- *"BISP se paise milenge, yahan click karein"*

Most people — especially elderly and low-literacy users — have no easy way to verify whether a message is genuine or a scam, and existing fraud-detection tools rarely support Roman Urdu.

## ✅ Solution

ScamShield PK lets a user paste a suspicious message, upload a screenshot, or check a phone number/link, and instantly returns:

- A **risk score** (Low / Suspicious / High)
- A list of specific **red flags** detected
- Simple **Roman Urdu advice** on what to do next

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 Message/Screenshot Checker | Paste text or upload a screenshot; AI extracts and analyzes it for scam patterns |
| 📊 Risk Score & Red Flags | Combines Gemini AI analysis with VirusTotal link scanning for a final risk verdict |
| 🕓 Session History | View previously checked messages in the current session |
| 📰 Trending Scams | Awareness cards showing common current scam patterns in Pakistan |
| ☎️ Contact Verifier | Basic check on whether a phone number follows official bank/company formats |

> **Note:** Login and history are session-based for demo purposes and are not backed by a persistent database. In a production version, these would be backed by a real authentication system and database.

---

## 🧱 Tech Stack

- **Frontend:** Streamlit
- **AI Engine:** Google Gemini API (text + vision)
- **Link Safety:** VirusTotal API
- **Deployment:** Streamlit Community Cloud

---

## 📂 Project Structure

```
scamshield-pk/
├── app.py                  # Main Streamlit app (UI + routing)
├── utils/
│   ├── gemini.py            # Gemini API integration (message/image analysis)
│   ├── virustotal.py        # VirusTotal link-checking integration
│   └── risk_engine.py       # Combines Gemini + VirusTotal into final risk score
├── data/
│   └── scams.json           # Trending scam examples (static data)
├── .env                     # Local API keys (not committed — see .gitignore)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root (never commit this file):

```
GEMINI_API_KEY=your_gemini_api_key_here
VIRUSTOTAL_API_KEY=your_virustotal_api_key_here
```

| API | Purpose | Get a Free Key |
|---|---|---|
| Gemini API | Analyzes message/screenshot text for scam patterns | [aistudio.google.com](https://aistudio.google.com) |
| VirusTotal API | Checks whether a link is malicious | [virustotal.com](https://www.virustotal.com) |

---

## 🚀 Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/syedmohtashimali-17/scamshield-pk.git
   cd scamshield-pk
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your `.env` file** (see above)

4. **Run the app locally**
   ```bash
   streamlit run app.py
   ```

---

## 👥 Team & Task Division

| Member | Responsibility |
|---|---|
| Person 1 | Frontend & main UI (login, dashboard, result display) |
| Person 2 | Gemini AI integration (message & screenshot analysis) |
| Person 3 | VirusTotal integration, risk score engine, contact verifier |
| Person 4 | History & trending scams UI, integration, deployment |

---

## 📄 Expected JSON Output Format

All AI analysis results follow this shared schema so modules can be developed independently:

```json
{
  "risk_level": "Low | Suspicious | High",
  "risk_score": 0,
  "scam_type": "type of scam detected",
  "red_flags": ["reason 1", "reason 2"],
  "explanation": "short explanation in English",
  "recommended_action": "what the user should do",
  "roman_urdu_advice": "advice in Roman Urdu"
}
```

---

## 🌐 Live Demo

_Deployment link will be added here once the app is live on Streamlit Community Cloud._

---

## ⚠️ Disclaimer

This project was built as a hackathon prototype. Login and history features are demonstration-only (session-based, no persistent database). It is intended to showcase AI-based scam detection and should not be used as a sole source of fraud verification.
