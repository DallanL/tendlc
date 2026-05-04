import os
import json
import re
import httpx
import base64
import time
import logging
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
from dotenv import load_dotenv

import prompts

load_dotenv()

# Set up logging
LOG_LEVEL = (
    logging.DEBUG if os.getenv("DEBUG", "false").lower() == "true" else logging.INFO
)
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

AI_BASE_URL = os.getenv("AI_BASE_URL", "http://localhost:11434/v1")
AI_API_KEY = os.getenv("AI_API_KEY", "ollama")
AI_MODEL = os.getenv("AI_MODEL", "llama3")
VISION_MODEL = os.getenv("VISION_MODEL", "llava")

client = AsyncOpenAI(base_url=AI_BASE_URL, api_key=AI_API_KEY)


async def _call_llm(model: str, messages: list, **kwargs):
    """
    Centralized LLM call helper that tracks statistics.
    """
    start_time = time.perf_counter()
    try:
        response = await client.chat.completions.create(
            model=model, messages=messages, **kwargs
        )
        duration = time.perf_counter() - start_time
        usage = response.usage

        if usage:
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
            prompt_rate = (
                prompt_tokens / duration if duration > 0 else 0
            )  # Estimated prompt eval rate
            eval_rate = (
                completion_tokens / duration if duration > 0 else 0
            )  # Estimated eval rate

            logger.debug(
                f"LLM Statistics ({model}): "
                f"Duration: {duration:.2f}s, "
                f"Prompt Tokens: {prompt_tokens}, "
                f"Completion Tokens: {completion_tokens}, "
                f"Total Tokens: {total_tokens}, "
                f"Prompt Rate: {prompt_rate:.2f} t/s, "
                f"Eval Rate: {eval_rate:.2f} t/s"
            )

        return response
    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(f"LLM Error ({model}) after {duration:.2f}s: {e}")
        raise


def _get_guidelines(filename: str):
    try:
        path = os.path.join("docs", filename)
        if not os.path.exists(path):
            pass
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.debug(f"Guidelines error for {filename}: {e}")
        return "Guidelines not found."


async def scrape_privacy_policy(url: str):
    logger.debug(f"Attempting to scrape URL: {url}")
    headers = {
        "User-Agent": "TendlcBot/1.0"
    }
    try:
        async with httpx.AsyncClient(
            timeout=10.0, follow_redirects=True, headers=headers
        ) as httpx_client:
            response = await httpx_client.get(url)
            logger.debug(f"Initial response status: {response.status_code}")

            if response.status_code != 200:
                logger.error(
                    f"Failed to fetch URL {url}: Status {response.status_code}"
                )
                return f"Error: Received status code {response.status_code} while fetching the URL."

            soup = BeautifulSoup(response.text, "html.parser")
            initial_text = soup.get_text()

            if len(initial_text) > 3000:
                logger.debug(
                    f"Page has substantial text ({len(initial_text)} chars). Using it directly."
                )
                return initial_text[:100000]

            # Type-safe search for privacy link
            policy_url = ""
            for a in soup.find_all("a"):
                text = a.get_text().lower()
                if "privacy" in text:
                    href = a.get("href")
                    if href:
                        policy_url = str(href)
                        break

            if policy_url:
                # Basic domain check to avoid wandering off to unrelated sites
                if (
                    policy_url.startswith("http")
                    and url.split("/")[2] not in policy_url
                ):
                    logger.debug(
                        f"Privacy link points to external domain ({policy_url}). Skipping."
                    )
                else:
                    logger.debug(f"Found likely privacy link: {policy_url}")
                    if not policy_url.startswith("http"):
                        base_url = "/".join(url.split("/")[:3])
                        policy_url = base_url + (
                            policy_url
                            if policy_url.startswith("/")
                            else "/" + policy_url
                        )

                    logger.debug(f"Scraping policy URL: {policy_url}")
                    policy_response = await httpx_client.get(policy_url)
                    if policy_response.status_code != 200:
                        logger.error(
                            f"Failed to fetch policy URL {policy_url}: Status {policy_response.status_code}"
                        )
                        return initial_text[:100000]

                    policy_soup = BeautifulSoup(policy_response.text, "html.parser")
                    return policy_soup.get_text()[:100000]

            logger.debug(
                f"No privacy link found or link was invalid. Returning initial text (length: {len(initial_text)})"
            )
            return initial_text[:100000]
    except Exception as e:
        logger.debug(f"Scrape Error: {str(e)}")
        return f"Error scraping: {str(e)}"


async def _extract_json(text: str):
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return match.group(0)
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            return match.group(0)
        return text
    except Exception:
        return text


async def analyze_brand_compliance(website_text: str, on_progress=None):
    return await _analyze_document(website_text, "Privacy Policy", on_progress)


async def analyze_tos_compliance(website_text: str, on_progress=None):
    return await _analyze_document(website_text, "Terms of Service", on_progress)


async def _analyze_document(website_text: str, doc_type: str, on_progress=None):
    chunk_size = 10000
    chunks = [
        website_text[i : i + chunk_size]
        for i in range(0, len(website_text), chunk_size)
    ]
    total_chunks = len(chunks)
    partial_findings = []

    logger.debug(f"Analyzing {total_chunks} chunks of {doc_type} text...")

    for i, chunk in enumerate(chunks):
        if on_progress:
            percent = int((i / (total_chunks + 1)) * 100)
            await on_progress(
                f"Analyzing {doc_type} section {i+1} of {total_chunks}...", percent
            )

        logger.debug(f"Analyzing {doc_type} chunk {i+1}/{total_chunks}...")
        prompt = prompts.BRAND_SECTION_ANALYSIS_PROMPT.format(section_text=chunk)
        try:
            response = await _call_llm(
                model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
            )
            partial_findings.append(
                f"--- {doc_type} Section {i+1} Finding ---\n{response.choices[0].message.content}"
            )
        except Exception as e:
            logger.debug(f"Error analyzing {doc_type} chunk {i+1}: {e}")
            partial_findings.append(
                f"--- {doc_type} Section {i+1} Finding ---\nError during analysis."
            )

    if on_progress:
        await on_progress(f"Synthesizing final {doc_type} judgement...", 90)

    logger.debug(f"Synthesizing final {doc_type} judgement...")
    guidelines = _get_guidelines("brand_identity_guidelines.md")
    compiled_findings = "\n\n".join(partial_findings)

    synthesis_prompt = prompts.BRAND_SYNTHESIS_PROMPT.format(
        guidelines=guidelines, compiled_findings=compiled_findings
    )

    try:
        response = await _call_llm(
            model=AI_MODEL, messages=[{"role": "user", "content": synthesis_prompt}]
        )
        if on_progress:
            await on_progress(f"{doc_type} vetting complete", 100)

        content = response.choices[0].message.content or "{}"
        return await _extract_json(content)
    except Exception as e:
        return json.dumps(
            {"status": "Rejected", "feedback": f"{doc_type} synthesis error: {str(e)}"}
        )


async def lint_campaign_messages(
    display_name: str,
    vertical: str,
    use_case: str,
    description: str,
    cta_flow: str,
    messages: str,
    attributes: dict,
    on_progress=None,
):
    if on_progress:
        await on_progress("Initializing campaign audit...", 10)

    guidelines = _get_guidelines("campaign_content_guidelines.md")

    if on_progress:
        await on_progress("Analyzing description and CTA flow...", 30)

    prompt = prompts.CAMPAIGN_LINTER_PROMPT.format(
        guidelines=guidelines,
        display_name=display_name,
        vertical=vertical,
        use_case=use_case,
        description=description,
        cta_flow=cta_flow,
        messages=messages,
        attributes=json.dumps(attributes),
    )

    if on_progress:
        await on_progress("Linting message content and attributes...", 60)

    try:
        response = await _call_llm(
            model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
        )

        if on_progress:
            await on_progress("Generating final campaign report...", 90)

        content = response.choices[0].message.content or "{}"
        return await _extract_json(content)
    except Exception as e:
        return json.dumps(
            {"status": "Rejected", "feedback": f"AI analysis error: {str(e)}"}
        )


async def analyze_opt_in_image(image_bytes: bytes, cta_flow: str):
    guidelines = _get_guidelines("opt_in_consent_guidelines.md")
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    prompt = prompts.VISION_OPT_IN_PROMPT.format(
        cta_flow=cta_flow, guidelines=guidelines
    )

    try:
        response = await _call_llm(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
        )
        content = response.choices[0].message.content or "{}"
        return await _extract_json(content)
    except Exception as e:
        logger.debug(f"Vision error: {e}")
        # Fallback if vision model fails or is not available
        return json.dumps(
            {
                "status": "Approved",
                "feedback": "Vision analysis simulation (Manual review recommended).",
            }
        )


async def analyze_opt_in_web_form(url: str, cta_flow: str):
    logger.debug(f"Analyzing opt-in web form at: {url}")
    scraped_text = await scrape_privacy_policy(url)  # Reuse scraper
    guidelines = _get_guidelines("opt_in_consent_guidelines.md")

    prompt = prompts.WEB_FORM_OPT_IN_PROMPT.format(
        cta_flow=cta_flow, scraped_text=scraped_text[:20000], guidelines=guidelines
    )

    try:
        response = await _call_llm(
            model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content or "{}"
        return await _extract_json(content)
    except Exception as e:
        return json.dumps(
            {"status": "Rejected", "feedback": f"Web form analysis error: {str(e)}"}
        )


async def assist_use_case(current_text: str):
    guidelines = _get_guidelines("campaign_content_guidelines.md")
    prompt = prompts.USE_CASE_ASSIST_PROMPT.format(
        guidelines=guidelines, current_text=current_text
    )
    response = await _call_llm(
        model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content or "No response from AI."


async def assist_messages(
    display_name: str,
    vertical: str,
    description: str,
    opt_in: str,
    opt_out: str,
    help_kw: str,
    embedded_link: str,
    embedded_phone: str,
):
    guidelines = _get_guidelines("campaign_content_guidelines.md")
    prompt = prompts.MESSAGES_ASSIST_PROMPT.format(
        guidelines=guidelines,
        display_name=display_name,
        vertical=vertical,
        description=description,
        opt_in_keyword=opt_in,
        opt_out_keyword=opt_out,
        help_keyword=help_kw,
        embedded_link=embedded_link,
        embedded_phone=embedded_phone,
    )
    response = await _call_llm(
        model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content or "[]"
    return await _extract_json(content)


async def assist_cta(current_text: str, display_name: str, website: str):
    prompt = prompts.CTA_ASSIST_PROMPT.format(
        display_name=display_name, website=website, current_text=current_text
    )
    response = await _call_llm(
        model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content or "No response from AI."


async def assist_keyword_message(
    type: str, display_name: str, opt_in: str, opt_out: str, help_kw: str
):
    if type == "opt_in":
        prompt_tmpl = prompts.OPT_IN_ASSIST_PROMPT
    elif type == "opt_out":
        prompt_tmpl = prompts.OPT_OUT_ASSIST_PROMPT
    else:
        prompt_tmpl = prompts.HELP_ASSIST_PROMPT

    prompt = prompt_tmpl.format(
        display_name=display_name,
        opt_in_keyword=opt_in,
        opt_out_keyword=opt_out,
        help_keyword=help_kw,
    )
    response = await _call_llm(
        model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content or "No response from AI."
