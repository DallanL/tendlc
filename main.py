import os
import json
import uuid
import markdown
import time
import logging
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Request, Form, UploadFile, File, BackgroundTasks
from fastapi.responses import (
    HTMLResponse,
    StreamingResponse,
    PlainTextResponse,
    JSONResponse,
)
from fastapi.templating import Jinja2Templates
from openai import AsyncOpenAI
from dotenv import load_dotenv

import ai_utils
import prompts
from schemas import CampaignDetails, CampaignAttributes

load_dotenv()

# Set up logging
LOG_LEVEL = logging.DEBUG if os.getenv("DEBUG", "false").lower() == "true" else logging.INFO
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

AI_BASE_URL = os.getenv("AI_BASE_URL", "http://localhost:11434/v1")
AI_API_KEY = os.getenv("AI_API_KEY", "ollama")
AI_MODEL = os.getenv("AI_MODEL", "llama3")
ENABLE_CHAT_WIDGET = os.getenv("ENABLE_CHAT_WIDGET", "false").lower() == "true"

app = FastAPI()
client = AsyncOpenAI(base_url=AI_BASE_URL, api_key=AI_API_KEY)
templates = Jinja2Templates(directory="templates")

# Background task states
brand_tasks: Dict[str, Any] = {}
campaign_tasks: Dict[str, Any] = {}


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "enable_chat": ENABLE_CHAT_WIDGET}
    )


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
        title = safe_name.replace("_", " ").replace(".md", "").title()
        return templates.TemplateResponse(
            "doc_view.html",
            {
                "request": request,
                "content": html_content,
                "title": title,
                "raw_text": text,
                "filename": safe_name.replace(".md", ""),
            },
        )
    except Exception:
        return HTMLResponse("Not found.", status_code=404)


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

        logger.debug(f"Starting brand analysis task {task_id}")

        for i, url in enumerate(urls):
            doc_type = "Privacy Policy" if i == 0 else "Terms & Conditions"
            brand_tasks[task_id]["status"] = f"Scraping {doc_type}..."
            website_text = await ai_utils.scrape_privacy_policy(url)

            async def on_progress(status, progress):
                total_progress = (i * 100 + progress) // len(urls)
                brand_tasks[task_id]["status"] = f"[{doc_type}] {status}"
                brand_tasks[task_id]["progress"] = total_progress

            func = (
                ai_utils.analyze_brand_compliance
                if i == 0
                else ai_utils.analyze_tos_compliance
            )
            result_raw = await func(website_text, on_progress)

            try:
                result = json.loads(result_raw)
                if not isinstance(result, dict):
                    result = {
                        "status": "Rejected",
                        "feedback": f"AI error: Got {type(result).__name__}",
                    }
                result["doc_type"] = doc_type
                brand_tasks[task_id]["results"].append(result)
            except Exception as e:
                brand_tasks[task_id]["results"].append(
                    {
                        "doc_type": doc_type,
                        "status": "Rejected",
                        "feedback": f"Error: {e}",
                    }
                )

        brand_tasks[task_id]["progress"] = 100
        logger.debug(f"Brand analysis task {task_id} completed.")

    background_tasks.add_task(run_analysis)
    return templates.TemplateResponse(
        "partials/brand_polling.html", {"request": request, "task_id": task_id}
    )


@app.get("/evaluate/brand/status/{task_id}", response_class=HTMLResponse)
async def evaluate_brand_status(request: Request, task_id: str):
    task = brand_tasks.get(task_id)
    if not task:
        return HTMLResponse("Not found", status_code=404)

    if task["progress"] == 100 and task["results"]:
        return templates.TemplateResponse(
            "partials/brand_report_multi.html",
            {"request": request, "results": task["results"]},
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


@app.post("/evaluate/campaign", response_class=HTMLResponse)
async def evaluate_campaign(
    background_tasks: BackgroundTasks,
    request: Request,
    display_name: str = Form(...),
    vertical: str = Form(...),
    selected_use_cases: List[str] = Form([]),
    is_high_volume: str = Form("no"),
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
    task_id = str(uuid.uuid4())
    campaign_tasks[task_id] = {
        "status": "Initializing...",
        "progress": 0,
        "result": None,
    }

    async def run_campaign_analysis():
        messages = [
            m
            for m in [
                sample_message_1,
                sample_message_2,
                sample_message_3,
                sample_message_4,
                sample_message_5,
            ]
            if m
        ]

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
            selected_use_cases=selected_use_cases,
            is_high_volume=is_high_volume.lower() == "yes",
            description=description,
            cta_flow=cta_flow,
            sample_messages=messages,
            embedded_link_sample=embedded_link_sample,
            attributes=attrs,
        )

        all_msgs = list(details.sample_messages)
        if details.attributes.opt_in_message:
            all_msgs.append(f"OPT-IN: {details.attributes.opt_in_message}")
        if details.attributes.opt_out_message:
            all_msgs.append(f"OPT-OUT: {details.attributes.opt_out_message}")
        if details.attributes.help_message:
            all_msgs.append(f"HELP: {details.attributes.help_message}")

        if not details.selected_use_cases:
            use_case_str = "None selected"
        elif len(details.selected_use_cases) == 1:
            use_case_str = details.selected_use_cases[0]
        else:
            use_case_str = f"{'Mixed' if details.is_high_volume else 'Low Volume Mixed'} ({', '.join(details.selected_use_cases)})"

        async def on_progress(status, progress):
            campaign_tasks[task_id]["status"] = status
            campaign_tasks[task_id]["progress"] = progress

        result_raw = await ai_utils.lint_campaign_messages(
            details.display_name,
            details.vertical,
            use_case_str,
            details.description,
            details.cta_flow,
            "\n---\n".join(all_msgs),
            details.attributes.model_dump(),
            on_progress,
        )

        try:
            campaign_tasks[task_id]["result"] = json.loads(result_raw)
        except Exception:
            campaign_tasks[task_id]["result"] = {
                "status": "Rejected",
                "feedback": f"AI Error: {result_raw}",
            }

        campaign_tasks[task_id]["progress"] = 100

    background_tasks.add_task(run_campaign_analysis)
    return templates.TemplateResponse(
        "partials/campaign_polling.html", {"request": request, "task_id": task_id}
    )


@app.get("/evaluate/campaign/status/{task_id}", response_class=HTMLResponse)
async def evaluate_campaign_status(request: Request, task_id: str):
    task = campaign_tasks.get(task_id)
    if not task:
        return HTMLResponse("Not found", status_code=404)

    if task["progress"] == 100 and task["result"]:
        result = task["result"]
        return templates.TemplateResponse(
            "partials/report_item.html",
            {
                "request": request,
                "title": "Campaign Compliance Vetting",
                "status": result.get("status", "Rejected"),
                "feedback": result.get("feedback", "Review required."),
            },
        )

    return templates.TemplateResponse(
        "partials/campaign_progress.html",
        {
            "request": request,
            "task_id": task_id,
            "status": task["status"],
            "progress": task["progress"],
        },
    )


@app.post("/assist/attribute-message/{attr_type}")
async def assist_attribute_message(request: Request, attr_type: str):
    form_data = await request.form()
    display_name = str(form_data.get("display_name") or "Brand")
    opt_in = str(form_data.get("subscriber_opt_in_keyword") or "START")
    opt_out = str(form_data.get("subscriber_opt_out_keyword") or "STOP")
    help_kw = str(form_data.get("subscriber_help_keyword") or "HELP")
    message = await ai_utils.assist_keyword_message(
        attr_type, display_name, opt_in, opt_out, help_kw
    )
    return PlainTextResponse(message)


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
                "feedback": "Provide upload or URL.",
            },
        )

    try:
        result = json.loads(result_raw)
    except Exception:
        result = {"status": "Rejected", "feedback": f"AI Error: {result_raw}"}

    return templates.TemplateResponse(
        "partials/report_item.html",
        {
            "request": request,
            "title": "Opt-In Proof Vetting",
            "status": result.get("status", "Rejected"),
            "feedback": result.get("feedback", "Manual review recommended."),
        },
    )


@app.get("/chat-stream")
async def chat_stream(request: Request, message: Optional[str] = None):
    if not message:
        return StreamingResponse(iter([]), media_type="text/event-stream")

    async def event_generator():
        start_time = time.perf_counter()
        token_count = 0
        try:
            response = await client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": prompts.SYSTEM_CHAT_PROMPT},
                    {"role": "user", "content": message},
                ],
                stream=True,
                stream_options={"include_usage": True}
            )
            async for chunk in response:
                # Handle usage if present in the final chunk
                if hasattr(chunk, 'usage') and chunk.usage:
                    duration = time.perf_counter() - start_time
                    usage = chunk.usage
                    prompt_tokens = usage.prompt_tokens
                    completion_tokens = usage.completion_tokens
                    logger.debug(
                        f"Stream Statistics ({AI_MODEL}): "
                        f"Duration: {duration:.2f}s, "
                        f"Prompt Tokens: {prompt_tokens}, "
                        f"Completion Tokens: {completion_tokens}, "
                        f"Eval Rate: {completion_tokens / duration:.2f} t/s"
                    )
                
                if chunk.choices and chunk.choices[0].delta.content:
                    token_count += 1
                    yield f"event: message\ndata: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"
            
            # Final stats if usage wasn't included or for general tracking
            duration = time.perf_counter() - start_time
            if token_count > 0:
                logger.debug(
                    f"Stream Finished ({AI_MODEL}): "
                    f"Duration: {duration:.2f}s, "
                    f"Estimated Chunks/Tokens: {token_count}, "
                    f"Estimated Rate: {token_count / duration:.2f} t/s"
                )
            
            yield f"event: message\ndata: {json.dumps({'content': '[DONE]'})}\n\n"
        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(f"Stream Error ({AI_MODEL}) after {duration:.2f}s: {e}")
            yield f"event: message\ndata: {json.dumps({'content': f'Error: {e}'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/assist/use-case")
async def assist_use_case_endpoint(use_case: str = Form("")):
    return PlainTextResponse(await ai_utils.assist_use_case(use_case))


@app.post("/assist/cta")
async def assist_cta_endpoint(
    cta_flow: str = Form(""), display_name: str = Form(""), website: str = Form("")
):
    return PlainTextResponse(await ai_utils.assist_cta(cta_flow, display_name, website))


@app.post("/assist/messages")
async def assist_messages_endpoint(request: Request):
    form_data = await request.form()
    display_name = str(form_data.get("display_name") or "Brand")
    vertical = str(form_data.get("vertical") or "Other")
    description = str(form_data.get("description") or "")
    opt_in = str(form_data.get("subscriber_opt_in_keyword") or "START")
    opt_out = str(form_data.get("subscriber_opt_out_keyword") or "STOP")
    help_kw = str(form_data.get("subscriber_help_keyword") or "HELP")
    embedded_link = str(form_data.get("embedded_link") or "no").upper()
    embedded_phone = str(form_data.get("embedded_phone") or "no").upper()

    raw_json = await ai_utils.assist_messages(
        display_name,
        vertical,
        description,
        opt_in,
        opt_out,
        help_kw,
        embedded_link,
        embedded_phone,
    )
    try:
        return JSONResponse(content=json.loads(raw_json))
    except Exception:
        return JSONResponse(content=[raw_json] + [""] * 4)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
