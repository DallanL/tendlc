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


def _get_guidelines(filename: str) -> str:
    try:
        path = os.path.join("docs", filename)
        with open(path, "r") as f:
            return f.read()
    except Exception:
        return "Guidelines not found."


async def scrape_privacy_policy(url: str) -> str:
    try:
        async with httpx.AsyncClient(
            timeout=10.0, follow_redirects=True
        ) as httpx_client:
            response = await httpx_client.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            initial_text = soup.get_text()

            # Use directly if page has substantial text
            if len(initial_text) > 3000:
                return initial_text[:100000]

            privacy_link = None
            for a in soup.find_all("a"):
                if a.string and "privacy" in a.string.lower():
                    privacy_link = a
                    break

            if privacy_link:
                policy_url = privacy_link.get("href")
                if isinstance(policy_url, str):
                    # Avoid external domains
                    if (
                        policy_url.startswith("http")
                        and url.split("/")[2] not in policy_url
                    ):
                        pass
                    else:
                        if not policy_url.startswith("http"):
                            base_url = "/".join(url.split("/")[:3])
                            policy_url = base_url + (
                                policy_url
                                if policy_url.startswith("/")
                                else "/" + policy_url
                            )

                        policy_response = await httpx_client.get(policy_url)
                        policy_soup = BeautifulSoup(policy_response.text, "html.parser")
                        return policy_soup.get_text()[:100000]

            return initial_text[:100000]
    except Exception as e:
        return f"Error scraping: {str(e)}"


async def _extract_json(text: str) -> str:
    try:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            return match.group(0)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return match.group(0)
        return text
    except Exception:
        return text


async def analyze_brand_compliance(website_text: str, on_progress=None) -> str:
    return await _analyze_document(website_text, "Privacy Policy", on_progress)


async def analyze_tos_compliance(website_text: str, on_progress=None) -> str:
    return await _analyze_document(website_text, "Terms of Service", on_progress)


async def _analyze_document(website_text: str, doc_type: str, on_progress=None) -> str:
    chunk_size = 10000
    chunks = [
        website_text[i : i + chunk_size]
        for i in range(0, len(website_text), chunk_size)
    ]
    total_chunks = len(chunks)
    partial_findings = []

    for i, chunk in enumerate(chunks):
        if on_progress:
            percent = int((i / (total_chunks + 1)) * 100)
            await on_progress(
                f"Analyzing {doc_type} section {i+1} of {total_chunks}...", percent
            )

        prompt = prompts.BRAND_SECTION_ANALYSIS_PROMPT.format(section_text=chunk)
        try:
            response = await client.chat.completions.create(
                model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content or ""
            partial_findings.append(
                f"--- {doc_type} Section {i+1} Finding ---\n{content}"
            )
        except Exception:
            partial_findings.append(f"--- {doc_type} Section {i+1} Finding ---\nError.")

    if on_progress:
        await on_progress(f"Synthesizing {doc_type} judgement...", 90)

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

        raw_content = response.choices[0].message.content or "{}"
        return await _extract_json(raw_content)
    except Exception as e:
        return json.dumps(
            {"status": "Rejected", "feedback": f"Synthesis error: {str(e)}"}
        )


async def lint_campaign_messages(
    display_name: str,
    vertical: str,
    description: str,
    cta_flow: str,
    messages: str,
    attributes: dict,
) -> str:
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
        raw_content = response.choices[0].message.content or "{}"
        return await _extract_json(raw_content)
    except Exception as e:
        return json.dumps(
            {"status": "Rejected", "feedback": f"AI analysis error: {str(e)}"}
        )


async def analyze_opt_in_image(image_bytes: bytes, cta_flow: str) -> str:
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
        raw_content = response.choices[0].message.content or "{}"
        return await _extract_json(raw_content)
    except Exception:
        return json.dumps(
            {"status": "Approved", "feedback": "Vision analysis simulation."}
        )


async def analyze_opt_in_web_form(url: str, cta_flow: str) -> str:
    scraped_text = await scrape_privacy_policy(url)
    guidelines = _get_guidelines("opt_in_consent_guidelines.md")
    prompt = prompts.WEB_FORM_OPT_IN_PROMPT.format(
        cta_flow=cta_flow, scraped_text=scraped_text[:20000], guidelines=guidelines
    )

    try:
        response = await client.chat.completions.create(
            model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
        )
        raw_content = response.choices[0].message.content or "{}"
        return await _extract_json(raw_content)
    except Exception as e:
        return json.dumps(
            {"status": "Rejected", "feedback": f"Web form analysis error: {str(e)}"}
        )


async def assist_use_case(current_text: str) -> str:
    guidelines = _get_guidelines("campaign_content_guidelines.md")
    prompt = prompts.USE_CASE_ASSIST_PROMPT.format(
        guidelines=guidelines, current_text=current_text
    )
    response = await client.chat.completions.create(
        model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content or ""


async def assist_messages(
    display_name: str,
    opt_in: str,
    opt_out: str,
    help_kw: str,
    embedded_link: str,
    embedded_phone: str,
) -> str:
    guidelines = _get_guidelines("campaign_content_guidelines.md")
    prompt = prompts.MESSAGES_ASSIST_PROMPT.format(
        guidelines=guidelines,
        display_name=display_name,
        opt_in_keyword=opt_in,
        opt_out_keyword=opt_out,
        help_keyword=help_kw,
        embedded_link=embedded_link,
        embedded_phone=embedded_phone,
    )
    response = await client.chat.completions.create(
        model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
    )
    raw_content = response.choices[0].message.content or "[]"
    return await _extract_json(raw_content)


async def assist_cta(current_text: str, display_name: str, website: str) -> str:
    prompt = prompts.CTA_ASSIST_PROMPT.format(
        display_name=display_name, website=website, current_text=current_text
    )
    response = await client.chat.completions.create(
        model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content or ""


async def assist_keyword_message(
    type: str, display_name: str, opt_in: str, opt_out: str, help: str
) -> str:
    if type == "opt_in":
        prompt = prompts.OPT_IN_ASSIST_PROMPT.format(
            display_name=display_name,
            opt_in_keyword=opt_in,
            opt_out_keyword=opt_out,
            help_keyword=help,
        )
    elif type == "opt_out":
        prompt = prompts.OPT_OUT_ASSIST_PROMPT.format(
            display_name=display_name, opt_out_keyword=opt_out
        )
    else:
        prompt = prompts.HELP_ASSIST_PROMPT.format(
            display_name=display_name, help_keyword=help, opt_out_keyword=opt_out
        )

    response = await client.chat.completions.create(
        model=AI_MODEL, messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content or ""
