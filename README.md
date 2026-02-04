# Interactive Micro-Experience (Flask + Vanilla JS)

A production-ready **Flask + Vanilla JavaScript** web app that showcases playful UX interactions, animation systems, and clean backend API design — built to demonstrate real-world frontend + backend engineering patterns.

This project focuses on:
- **Responsive UI** (mobile Safari/Chrome friendly)
- **Pointer + touch event handling**
- **Canvas-based confetti animation** (no external libraries)
- **Backend API endpoint** with optional server-side LLM integrations
- **Deployment-ready setup** (Gunicorn + Procfile)

---

## ✨ What it does

### UI / UX
- Landing page asks a question with **Yes / No** choices
- **“No” button evades** the cursor/touch to make it difficult to click
- Clicking **Yes**:
  1) Locks the UI
  2) Plays a **toy pop animation** (emoji/CSS, no external assets)
  3) Runs a **confetti celebration** using **vanilla JS + canvas**
  4) Displays **only a single quote** (no author)

### Backend
- `GET /` serves the UI
- `POST /api/yes` returns JSON:
  - `quote` (string)
  - `citation` (string or null, optional)
  - `openai_line` (string, optional)

If API keys are missing, it falls back to a local quote and still works.

---

## 🧠 What this project showcases

- **Frontend engineering**
  - Touch-friendly interactions (`pointer` + `touch` events)
  - Viewport-safe button positioning
  - Accessible markup (ARIA labels)
  - Reduced motion support (`prefers-reduced-motion`)

- **Animation systems**
  - Canvas confetti using `requestAnimationFrame`
  - Lightweight animation logic with performance awareness

- **Backend engineering**
  - Flask route structure + JSON API
  - Safe fallbacks + clean environment-based configuration

- **Security**
  - API keys are **server-side only**
  - `.env` is **never committed**
  - `.env.example` is provided for setup

---

## ✅ Tech Stack

- **Backend:** Python + Flask  
- **Frontend:** HTML/CSS + Vanilla JS  
- **Animations:** CSS + Canvas  
- **Deployment:** Gunicorn + Procfile (Render/Fly/Heroku style)

---

## 🚀 Run locally

### 1) Clone repo
```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
2) Create virtualenv + install
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
3) Add environment variables (optional)
Create .env locally (DO NOT commit it):

cp .env.example .env
Edit .env and add your keys (optional):

OPENAI_API_KEY=...
PERPLEXITY_API_KEY=...
4) Run the server
PORT=5050 python app.py
Open:

