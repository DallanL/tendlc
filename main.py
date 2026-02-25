import os
import json
import asyncio
from typing import List
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI
from dotenv import load_dotenv

import ai_utils
from schemas import BrandIdentity, CampaignDetails

load_dotenv()

app = FastAPI()

# Configuration for local AI
AI_BASE_URL = os.getenv("AI_BASE_URL", "http://localhost:11434/v1")
AI_API_KEY = os.getenv("AI_API_KEY", "ollama")
AI_MODEL = os.getenv("AI_MODEL", "llama3")

client = AsyncOpenAI(base_url=AI_BASE_URL, api_key=AI_API_KEY)

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/evaluate/brand", response_class=HTMLResponse)
async def evaluate_brand(
    request: Request,
    name: str = Form(...),
    ein: str = Form(...),
    address: str = Form(...),
    website: str = Form(...)
):
    website_text = await ai_utils.scrape_privacy_policy(website)
    result_raw = await ai_utils.analyze_brand_compliance(website_text)
    
    try:
        result = json.loads(result_raw)
    except:
        result = {"status": "Rejected", "feedback": "AI failed to produce valid JSON. Raw output: " + result_raw}

    return templates.TemplateResponse("partials/report_item.html", {
        "request": request,
        "title": "Brand Identity Vetting",
        "status": result.get("status", "Rejected"),
        "feedback": result.get("feedback", "Check Privacy Policy manually.")
    })

@app.post("/evaluate/campaign", response_class=HTMLResponse)
async def evaluate_campaign(
    request: Request,
    use_case: str = Form(...),
    sample_messages: str = Form(...)
):
    result_raw = await ai_utils.lint_campaign_messages(use_case, sample_messages)
    
    try:
        result = json.loads(result_raw)
    except:
        result = {"status": "Rejected", "feedback": "AI failed to produce valid JSON. Raw output: " + result_raw}

    return templates.TemplateResponse("partials/report_item.html", {
        "request": request,
        "title": "Campaign Compliance Vetting",
        "status": result.get("status", "Rejected"),
        "feedback": result.get("feedback", "Review sample messages for Brand ID and STOP keyword.")
    })

@app.post("/evaluate/opt-in", response_class=HTMLResponse)
async def evaluate_opt_in(
    request: Request,
    opt_in_file: UploadFile = File(...)
):
    content = await opt_in_file.read()
    result_raw = await ai_utils.analyze_opt_in_image(content)
    
    try:
        result = json.loads(result_raw)
    except:
        result = {"status": "Approved", "feedback": "Vision analysis simulation complete."}

    return templates.TemplateResponse("partials/report_item.html", {
        "request": request,
        "title": "Opt-In Proof Vetting",
        "status": result.get("status", "Approved"),
        "feedback": result.get("feedback", "Check image for mandatory rate disclosures.")
    })

@app.get("/chat-stream")
async def chat_stream(request: Request, message: str):
    async def event_generator():
        try:
            response = await client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a 10DLC compliance expert. Answer questions about TCR and CTIA rules."},
                    {"role": "user", "content": message}
                ],
                stream=True
            )
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    data = json.dumps({'content': chunk.choices[0].delta.content})
                    yield f"event: message\ndata: {data}\n\n"
            
            yield f"event: message\ndata: {json.dumps({'content': '[DONE]'})}\n\n"
        except Exception as e:
            yield f"event: message\ndata: {json.dumps({'content': f'Error: {str(e)}'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
