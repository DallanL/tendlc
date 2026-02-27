# 10DLC Pre-Vetting & Registration Portal

A lightweight, AI-powered portal for strict 2026 CTIA and TCR compliance vetting. This utility allows users to submit business details and SMS campaign data for automated evaluation by a multi-agent AI backend.

## ✨ Features

- **Multi-Stage Brand Vetting**: Independent analysis of Privacy Policies and Terms of Service using a sliding context window (up to 100k characters).
- **Campaign Content Linter**: Strict cross-validation of campaign descriptions, step-by-step CTA flows, and sample messages against TCR standards.
- **Hybrid Opt-In Verification**: Supports both screenshot analysis (Vision-Language Model) and direct web form scraping.
- **AI Assist Tools**: Intelligent buttons to professionally expand use cases, message flows, and mandatory opt-in/out/help keywords.
- **Session Persistence**: Automatically saves and restores all form progress using browser local storage.
- **Markdown Export**: Download your completed application as a professionally formatted `.txt` file for easy submission.

## 🚀 Deployment

### Local Development

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   Copy `.env.example` to `.env` and update the variables.
   ```bash
   cp .env.example .env
   ```

3. **Run with Uvicorn:**
   ```bash
   uvicorn main:app --reload
   ```

### Docker (Recommended for Production)

1. **Build and Launch:**
   ```bash
   docker compose up -d --build
   ```
   *The application is configured with Traefik labels for automated HTTPS and proxying.*

## 🧠 LLM Integration

The portal uses the OpenAI Python SDK and is model-agnostic. It can point to any local or remote provider that supports an OpenAI-compatible API.

### Local Models (Recommended)

To keep your data private and avoid API costs, use local inference servers:

- **Ollama**:
  - `AI_BASE_URL=http://localhost:11434/v1`
  - **Text Model**: `qwen2.5:8b` or `qwen2.5:14b` (Highly recommended for strict instruction following).
  - **Vision Model**: `llama3.2-vision:11b` (Required for screenshot verification).
- **vLLM**: Perfect for dual-GPU setups. Point `AI_BASE_URL` to your vLLM endpoint.

### Remote Providers

- **OpenAI**: Set `AI_BASE_URL` to `https://api.openai.com/v1` and provide your `AI_API_KEY`.
- **Groq/Together/OpenRouter**: Point the base URL to their respective OpenAI-compatible endpoints.

## 🛠️ Usage

1. **Brand Identity**: Fill out your legal entity details. Submit for "Full Brand Compliance" to trigger the automated Privacy/ToS audit.
2. **Campaign Details**: Describe your campaign. Use the **AI Assist** buttons to refine your descriptions and message flows.
3. **Keywords**: Define your START/STOP/HELP keywords. Use the assist tool to generate TCR-compliant response messages.
4. **Validation**: Click "Validate Campaign" to run the AI compliance linter.
5. **Opt-In Proof**: Upload a screenshot or point to your web form URL for final verification.
6. **Save**: Use the sidebar to "Save Application" and download your registration as a Markdown file.

## 🛡️ Code Quality

Run the following to ensure everything is production-ready:
```bash
make check  # Runs Black, Ruff, and Mypy
```
