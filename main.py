import os
import json
import uuid
import markdown
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Form, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from openai import AsyncOpenAI
from dotenv import load_dotenv

import ai_utils
import prompts
from schemas import CampaignDetails, CampaignAttributes

load_dotenv()

# Configuration for local AI
AI_BASE_URL = os.getenv("AI_BASE_URL", "http://localhost:11434/v1")
AI_API_KEY = os.getenv("AI_API_KEY", "ollama")
AI_MODEL = os.getenv("AI_MODEL", "llama3")

app = FastAPI()

client = AsyncOpenAI(base_url=AI_BASE_URL, api_key=AI_API_KEY)

templates = Jinja2Templates(directory="templates")

# Task storage for progress tracking
brand_tasks: Dict[str, Any] = {}


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/docs/{doc_name}", response_class=HTMLResponse)
async def serve_doc(request: Request, doc_name: str):
    try:
        safe_name = os.path.basename(doc_name)
        if not safe_name.endswith(".md"):
            safe_name += ".md"

        file_path = os.path.join("docs", safe_name)

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        html_content = markdown.markdown(text)

        return templates.TemplateResponse(
            "doc_view.html",
            {
                "request": request,
                "content": html_content,
                "title": safe_name.replace("_", " ").replace(".md", "").title(),
            },
        )
    except Exception:
        return HTMLResponse("Document not found.", status_code=404)


@app.post("/evaluate/brand", response_class=HTMLResponse)
async def evaluate_brand(
    background_tasks: BackgroundTasks,
    request: Request,
    legal_name: str = Form(...),
    dba_name: Optional[str] = Form(None),
    legal_form: str = Form(...),
    country_of_registration: str = Form(...),
    ein: str = Form(...),
    tax_id_issuing_country: str = Form(...),
    alt_business_id_type: str = Form(...),
    alt_business_id: Optional[str] = Form(None),
    address: str = Form(...),
    website_url: str = Form(...),
    privacy_policy_url: str = Form(...),
    terms_and_conditions_url: str = Form(...),
    stock_symbol: Optional[str] = Form(None),
    stock_exchange: Optional[str] = Form(None),
    contact_first_name: str = Form(...),
    contact_last_name: str = Form(...),
    contact_email: str = Form(...),
    contact_phone: str = Form(...),
):
    task_id = str(uuid.uuid4())
    brand_tasks[task_id] = {"status": "Initializing...", "progress": 0, "results": []}

    async def run_analysis():
        urls = [privacy_policy_url]
        if terms_and_conditions_url != privacy_policy_url:
            urls.append(terms_and_conditions_url)

        for i, url in enumerate(urls):
            doc_type = "Privacy Policy" if i == 0 else "Terms & Conditions"
            brand_tasks[task_id]["status"] = f"Scraping {doc_type}..."

            website_text = await ai_utils.scrape_privacy_policy(url)

            async def on_progress(status, progress):
                # Adjust progress to account for multiple URLs
                total_progress = (i * 100 + progress) // len(urls)
                brand_tasks[task_id]["status"] = f"[{doc_type}] {status}"
                brand_tasks[task_id]["progress"] = total_progress

            result_raw = await (
                ai_utils.analyze_brand_compliance(website_text, on_progress)
                if i == 0
                else ai_utils.analyze_tos_compliance(website_text, on_progress)
            )

            try:
                result = json.loads(result_raw)
                result["doc_type"] = doc_type
                brand_tasks[task_id]["results"].append(result)
            except Exception as e:
                brand_tasks[task_id]["results"].append(
                    {
                        "doc_type": doc_type,
                        "status": "Rejected",
                        "feedback": f"AI failed to produce valid JSON: {str(e)}",
                    }
                )

        brand_tasks[task_id]["progress"] = 100

    background_tasks.add_task(run_analysis)

    return templates.TemplateResponse(
        "partials/brand_polling.html", {"request": request, "task_id": task_id}
    )


@app.get("/evaluate/brand/status/{task_id}", response_class=HTMLResponse)
async def evaluate_brand_status(request: Request, task_id: str):
    task = brand_tasks.get(task_id)
    if not task:
        return HTMLResponse("Task not found", status_code=404)

    if task["progress"] == 100 and task["results"]:
        return templates.TemplateResponse(
            "partials/brand_report_multi.html",
            {
                "request": request,
                "results": task["results"],
            },
        )

    return templates.TemplateResponse(
        "partials/brand_progress.html",
        {
            "request": request,
            "task_id": task_id,
            "status": task["status"],
            "progress": task["progress"],
        },
    )


@app.post("/assist/attribute-message/{attr_type}")
async def assist_attribute_message(
    attr_type: str, display_name: str = Form(...), keyword: str = Form(...)
):
    print(f"DEBUG: AI Assist requested for {attr_type}. Keyword: {keyword}")
    message = await ai_utils.assist_keyword_message(attr_type, display_name, keyword)
    return PlainTextResponse(message)


@app.post("/evaluate/campaign", response_class=HTMLResponse)
async def evaluate_campaign(
    request: Request,
    display_name: str = Form(...),
    vertical: str = Form(...),
    description: str = Form(...),
    cta_flow: str = Form(...),
    sample_message_1: str = Form(...),
    sample_message_2: str = Form(...),
    sample_message_3: Optional[str] = Form(None),
    sample_message_4: Optional[str] = Form(None),
    sample_message_5: Optional[str] = Form(None),
    embedded_link_sample: Optional[str] = Form(None),
    subscriber_opt_in: str = Form(...),
    opt_in_keyword: Optional[str] = Form(None),
    opt_in_message: Optional[str] = Form(None),
    subscriber_opt_out: str = Form(...),
    opt_out_keyword: Optional[str] = Form(None),
    opt_out_message: Optional[str] = Form(None),
    subscriber_help: str = Form(...),
    help_keyword: Optional[str] = Form(None),
    help_message: Optional[str] = Form(None),
    number_pooling: str = Form(...),
    direct_lending: str = Form(...),
    embedded_link: str = Form(...),
    embedded_phone: str = Form(...),
    affiliate_marketing: str = Form(...),
    age_gated: str = Form(...),
):
    # Map messages
    messages = [sample_message_1, sample_message_2]
    if sample_message_3:
        messages.append(sample_message_3)
    if sample_message_4:
        messages.append(sample_message_4)
    if sample_message_5:
        messages.append(sample_message_5)

    # Map attributes
    attrs = CampaignAttributes(
        subscriber_opt_in=subscriber_opt_in.lower() == "yes",
        opt_in_keyword=opt_in_keyword,
        opt_in_message=opt_in_message,
        subscriber_opt_out=subscriber_opt_out.lower() == "yes",
        opt_out_keyword=opt_out_keyword,
        opt_out_message=opt_out_message,
        subscriber_help=subscriber_help.lower() == "yes",
        help_keyword=help_keyword,
        help_message=help_message,
        number_pooling=number_pooling.lower() == "yes",
        direct_lending=direct_lending.lower() == "yes",
        embedded_link=embedded_link.lower() == "yes",
        embedded_phone=embedded_phone.lower() == "yes",
        affiliate_marketing=affiliate_marketing.lower() == "yes",
        age_gated=age_gated.lower() == "yes",
    )

    details = CampaignDetails(
        display_name=display_name,
        vertical=vertical,
        description=description,
        cta_flow=cta_flow,
        sample_messages=messages,
        embedded_link_sample=embedded_link_sample,
        attributes=attrs,
    )

    # Include special messages in the analysis context
    all_context_messages = list(details.sample_messages)
    if details.attributes.opt_in_message:
        all_context_messages.append(f"OPT-IN: {details.attributes.opt_in_message}")
    if details.attributes.opt_out_message:
        all_context_messages.append(f"OPT-OUT: {details.attributes.opt_out_message}")
    if details.attributes.help_message:
        all_context_messages.append(f"HELP: {details.attributes.help_message}")

    result_raw = await ai_utils.lint_campaign_messages(
        details.display_name,
        details.vertical,
        details.description,
        details.cta_flow,
        "\n---\n".join(all_context_messages),
        details.attributes.dict(),
    )

    try:
        result = json.loads(result_raw)
    except Exception:
        result = {
            "status": "Rejected",
            "feedback": "AI failed to produce valid JSON. Raw output: "
            + str(result_raw),
        }

    return templates.TemplateResponse(
        "partials/report_item.html",
        {
            "request": request,
            "title": "Campaign Compliance Vetting",
            "status": result.get("status", "Rejected"),
            "feedback": result.get(
                "feedback", "Review sample messages for Brand ID and STOP keyword."
            ),
        },
    )


@app.post("/evaluate/opt-in", response_class=HTMLResponse)
async def evaluate_opt_in(
    request: Request,
    cta_flow: str = Form(...),
    opt_in_file: Optional[UploadFile] = File(None),
    opt_in_url: Optional[str] = Form(None),
):
    if opt_in_file and opt_in_file.filename:
        content = await opt_in_file.read()
        result_raw = await ai_utils.analyze_opt_in_image(content, cta_flow)
    elif opt_in_url:
        result_raw = await ai_utils.analyze_opt_in_web_form(opt_in_url, cta_flow)
    else:
        return templates.TemplateResponse(
            "partials/report_item.html",
            {
                "request": request,
                "title": "Opt-In Proof Vetting",
                "status": "Rejected",
                "feedback": "Please provide either a screenshot upload or a web form URL.",
            },
        )

    try:
        result = json.loads(result_raw)
    except Exception:
        result = {
            "status": "Rejected",
            "feedback": "AI failed to produce valid JSON. Raw output: "
            + str(result_raw),
        }

    return templates.TemplateResponse(
        "partials/report_item.html",
        {
            "request": request,
            "title": "Opt-In Proof Vetting",
            "status": result.get("status", "Rejected"),
            "feedback": result.get("feedback", "Check opt-in proof manually."),
        },
    )


@app.get("/chat-stream")
async def chat_stream(request: Request, message: Optional[str] = None):
    if not message:
        return StreamingResponse(iter([]), media_type="text/event-stream")

    async def event_generator():
        try:
            response = await client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": prompts.SYSTEM_CHAT_PROMPT},
                    {"role": "user", "content": message},
                ],
                stream=True,
            )
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    data = json.dumps({"content": chunk.choices[0].delta.content})
                    yield f"event: message\ndata: {data}\n\n"

            yield f"event: message\ndata: {json.dumps({'content': '[DONE]'})}\n\n"
        except Exception as e:
            yield f"event: message\ndata: {json.dumps({'content': f'Error: {str(e)}'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/assist/use-case")
async def assist_use_case_endpoint(use_case: str = Form("")):
    improved_text = await ai_utils.assist_use_case(use_case)
    return PlainTextResponse(improved_text)


@app.post("/assist/cta")
async def assist_cta_endpoint(
    cta_flow: str = Form(""), display_name: str = Form(""), website: str = Form("")
):
    print(f"DEBUG: AI Assist requested for CTA. Input length: {len(cta_flow)}")
    improved_cta = await ai_utils.assist_cta(cta_flow, display_name, website)
    print(f"DEBUG: AI Assist returned improved CTA (length: {len(improved_cta)})")
    return PlainTextResponse(improved_cta)


@app.post("/assist/messages")
async def assist_messages_endpoint(sample_messages: str = Form("")):
    print(
        f"DEBUG: AI Assist requested for Messages. Input length: {len(sample_messages)}"
    )
    improved_messages = await ai_utils.assist_messages(sample_messages)
    print(
        f"DEBUG: AI Assist returned improved Messages (length: {len(improved_messages)})"
    )
    return PlainTextResponse(improved_messages)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
