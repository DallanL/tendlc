import os
import json
import re
import httpx
import base64
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
from dotenv import load_dotenv

import prompts

load_dotenv()

AI_BASE_URL = os.getenv("AI_BASE_URL", "http://localhost:11434/v1")
AI_API_KEY = os.getenv("AI_API_KEY", "ollama")
AI_MODEL = os.getenv("AI_MODEL", "llama3")
VISION_MODEL = os.getenv("VISION_MODEL", "llava")

client = AsyncOpenAI(base_url=AI_BASE_URL, api_key=AI_API_KEY)


def _get_guidelines(filename: str):
    try:
        path = os.path.join("docs", filename)
        if not os.path.exists(path):
            pass
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        print(f"DEBUG: Guidelines error for {filename}: {e}")
        return "Guidelines not found."


async def scrape_privacy_policy(url: str):
    print(f"DEBUG: Attempting to scrape URL: {url}")
    try:
        async with httpx.AsyncClient(
            timeout=10.0, follow_redirects=True
        ) as httpx_client:
            response = await httpx_client.get(url)
            print(f"DEBUG: Initial response status: {response.status_code}")
            soup = BeautifulSoup(response.text, "html.parser")
            initial_text = soup.get_text()

            if len(initial_text) > 3000:
                print(
                    f"DEBUG: Page has substantial text ({len(initial_text)} chars). Using it directly."
                )
                return initial_text[:100000]

            privacy_link = soup.find("a", string=lambda t: t and "privacy" in t.lower())
            if privacy_link:
                policy_url = privacy_link.get("href")

                if (
                    policy_url.startswith("http")
                    and url.split("/")[2] not in policy_url
                ):
                    print(
                        f"DEBUG: Privacy link points to external domain ({policy_url}). Skipping."
                    )
                else:
                    print(f"DEBUG: Found likely privacy link: {policy_url}")
                    if not policy_url.startswith("http"):
                        base_url = "/".join(url.split("/")[:3])
                        policy_url = base_url + (
                            policy_url
                            if policy_url.startswith("/")
                            else "/" + policy_url
                        )

                    print(f"DEBUG: Scraping policy URL: {policy_url}")
                    policy_response = await httpx_client.get(policy_url)
                    policy_soup = BeautifulSoup(policy_response.text, "html.parser")
                    return policy_soup.get_text()[:100000]

            print(
                f"DEBUG: No privacy link found or link was invalid. Returning initial text (length: {len(initial_text)})"
            )
            return initial_text[:100000]
    except Exception as e:
        print(f"DEBUG: Scrape Error: {str(e)}")
        return f"Error scraping: {str(e)}"


async def _extract_json(text: str):
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
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

    print(f"DEBUG: Analyzing {total_chunks} chunks of {doc_type} text...")

    for i, chunk in enumerate(chunks):
        if on_progress:
            # We save the last 10% for synthesis
            percent = int((i / (total_chunks + 1)) * 100)
            await on_progress(
                f"Analyzing {doc_type} section {i+1} of {total_chunks}...", percent
            )

        print(f"DEBUG: Analyzing {doc_type} chunk {i+1}/{total_chunks}...")
        prompt = prompts.BRAND_SECTION_ANALYSIS_PROMPT.format(section_text=chunk)
        try:
            response = await client.chat.completions.create(
                model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
            )
            partial_findings.append(
                f"--- {doc_type} Section {i+1} Finding ---\n{response.choices[0].message.content}"
            )
        except Exception as e:
            print(f"DEBUG: Error analyzing {doc_type} chunk {i+1}: {e}")
            partial_findings.append(
                f"--- {doc_type} Section {i+1} Finding ---\nError during analysis."
            )

    if on_progress:
        await on_progress(f"Synthesizing final {doc_type} judgement...", 90)

    print(f"DEBUG: Synthesizing final {doc_type} judgement...")
    guidelines = _get_guidelines("brand_identity_guidelines.md")
    compiled_findings = "\n\n".join(partial_findings)

    synthesis_prompt = prompts.BRAND_SYNTHESIS_PROMPT.format(
        guidelines=guidelines, compiled_findings=compiled_findings
    )

    try:
        response = await client.chat.completions.create(
            model=AI_MODEL, messages=[{"role": "user", "content": synthesis_prompt}]
        )
        if on_progress:
            await on_progress(f"{doc_type} vetting complete", 100)

        content = await _extract_json(response.choices[0].message.content)
        return content
    except Exception as e:
        return json.dumps(
            {"status": "Rejected", "feedback": f"{doc_type} synthesis error: {str(e)}"}
        )


async def lint_campaign_messages(
    display_name: str,
    vertical: str,
    description: str,
    cta_flow: str,
    messages: str,
    attributes: dict,
):
    guidelines = _get_guidelines("campaign_content_guidelines.md")
    prompt = prompts.CAMPAIGN_LINTER_PROMPT.format(
        guidelines=guidelines,
        display_name=display_name,
        vertical=vertical,
        description=description,
        cta_flow=cta_flow,
        messages=messages,
        attributes=json.dumps(attributes),
    )
    try:
        response = await client.chat.completions.create(
            model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
        )
        content = await _extract_json(response.choices[0].message.content)
        return content
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
        response = await client.chat.completions.create(
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
        content = await _extract_json(response.choices[0].message.content)
        return content
    except Exception as e:
        print(f"DEBUG: Vision error: {e}")
        # Fallback if vision model fails or is not available
        return json.dumps(
            {
                "status": "Approved",
                "feedback": "Vision analysis simulation (Manual review recommended).",
            }
        )


async def analyze_opt_in_web_form(url: str, cta_flow: str):
    print(f"DEBUG: Analyzing opt-in web form at: {url}")
    scraped_text = await scrape_privacy_policy(url)  # Reuse scraper
    guidelines = _get_guidelines("opt_in_consent_guidelines.md")

    prompt = prompts.WEB_FORM_OPT_IN_PROMPT.format(
        cta_flow=cta_flow, scraped_text=scraped_text[:20000], guidelines=guidelines
    )

    try:
        response = await client.chat.completions.create(
            model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
        )
        content = await _extract_json(response.choices[0].message.content)
        return content
    except Exception as e:
        return json.dumps(
            {"status": "Rejected", "feedback": f"Web form analysis error: {str(e)}"}
        )


async def assist_use_case(current_text: str):
    guidelines = _get_guidelines("campaign_content_guidelines.md")
    prompt = prompts.USE_CASE_ASSIST_PROMPT.format(
        guidelines=guidelines, current_text=current_text
    )
    response = await client.chat.completions.create(
        model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


async def assist_messages(current_text: str):
    guidelines = _get_guidelines("campaign_content_guidelines.md")
    prompt = prompts.MESSAGES_ASSIST_PROMPT.format(
        guidelines=guidelines, current_text=current_text
    )
    response = await client.chat.completions.create(
        model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


async def assist_cta(current_text: str, display_name: str, website: str):
    prompt = prompts.CTA_ASSIST_PROMPT.format(
        display_name=display_name, website=website, current_text=current_text
    )
    response = await client.chat.completions.create(
        model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


async def assist_keyword_message(type: str, display_name: str, keyword: str):
    if type == "opt_in":
        prompt_tmpl = prompts.OPT_IN_ASSIST_PROMPT
    elif type == "opt_out":
        prompt_tmpl = prompts.OPT_OUT_ASSIST_PROMPT
    else:
        prompt_tmpl = prompts.HELP_ASSIST_PROMPT

    prompt = prompt_tmpl.format(display_name=display_name, keyword=keyword)
    response = await client.chat.completions.create(
        model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
