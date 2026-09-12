# ScamShield PK 🛡️

An AI-powered tool that checks suspicious SMS/WhatsApp messages, screenshots, links, and
phone numbers common in Pakistan, and gives simple Roman Urdu advice on whether they're a scam.

## File Structure

```
scamshield-pk/
├── app.py                   # Main Streamlit app (UI + integration) — Person 1 & 4
├── utils/
│   ├── __init__.py
│   ├── gemini.py             # Gemini AI analysis — Person 2
│   ├── virustotal.py         # VirusTotal URL check — Person 3 (add this file)
│   └── risk_engine.py        # Combines Gemini + VirusTotal into final score — Person 3
├── data/
│   └── scams.json            # Trending scams data — Person 4
├── .env.example               # Template for required API keys
├── .gitignore
├── requirements.txt
└── README.md
```

## Local Setup

1. Clone the repo and enter the folder:
   ```bash
   git clone https://github.com/<your-username>/scamshield-pk.git
   cd scamshield-pk
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your real keys:
   ```bash
   cp .env.example .env
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Getting API Keys (Free)

| API | Purpose | Where to get it |
|---|---|---|
| Gemini API | Analyze message/screenshot text | [aistudio.google.com](https://aistudio.google.com) → sign in with Google → "Get API key" |
| VirusTotal API | Check if a link is malicious | [virustotal.com](https://virustotal.com) → create free account → API key in profile (4 req/min, 500/day) |

**Never commit `.env` to GitHub.** It is already listed in `.gitignore`.

## Deploying to Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
2. Click **"New app"** and select the `scamshield-pk` repository, branch (`main`), and main file (`app.py`).
3. Before or after deploying, open the app's **Settings → Secrets** and paste:
   ```toml
   GEMINI_API_KEY = "your_real_gemini_key"
   VIRUSTOTAL_API_KEY = "your_real_virustotal_key"
   ```
   Streamlit exposes these as environment variables automatically at runtime — no code changes needed since `app.py` reads keys via `os.environ.get(...)` inside `utils/gemini.py` and `utils/risk_engine.py`.
4. Click **Deploy**. In a few minutes you'll get a live public link (e.g. `https://scamshield-pk.streamlit.app`) to share with judges.
5. Every time someone pushes to the connected GitHub branch, Streamlit Cloud auto-redeploys.

## Notes

- This is a hackathon demo: login and history are session-only (`st.session_state`), no real database or authentication.
- `utils/gemini.py` and `utils/risk_engine.py` currently contain **mock/placeholder logic** so the full app runs end-to-end even before Person 2 and Person 3 finish their real implementations. They must keep the same function names and return shapes when replacing the mock logic (see the agreed JSON contract in each file's docstring).
