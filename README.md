# 10DLC Pre-Vetting & Registration Portal

A lightweight, AI-powered portal for 2026 CTIA and TCR compliance vetting.

## Tech Stack
- **Backend:** FastAPI (Python)
- **Frontend:** HTML, Jinja2, HTMX, Tailwind CSS
- **AI Integration:** OpenAI SDK (model-agnostic, points to local vLLM/Ollama)

## Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Local AI:**
   Copy `.env.example` to `.env` and update the `AI_BASE_URL` and `AI_MODEL` to match your local setup (e.g., Ollama or vLLM).

3. **Run the Application:**
   ```bash
   python main.py
   ```
   Or using uvicorn:
   ```bash
   uvicorn main:app --reload
   ```

4. **Access the Portal:**
   Open `http://localhost:8000` in your browser.

## Features
- **Brand Vetting:** Automated website scraping and Privacy Policy analysis.
- **Campaign Linter:** Checks message content for Brand ID, Opt-out language, and SHAFT violations.
- **Opt-In Validator:** Vision-Language Model analysis of consent flow screenshots.
- **Compliance Chat:** Real-time streaming assistant for 10DLC guidance.
