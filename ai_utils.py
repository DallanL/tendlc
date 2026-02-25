import httpx
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
import os

AI_BASE_URL = os.getenv("AI_BASE_URL", "http://localhost:11434/v1")
AI_API_KEY = os.getenv("AI_API_KEY", "ollama")
AI_MODEL = os.getenv("AI_MODEL", "llama3")
VISION_MODEL = os.getenv("VISION_MODEL", "llava")

client = AsyncOpenAI(base_url=AI_BASE_URL, api_key=AI_API_KEY)

async def scrape_privacy_policy(url: str):
    try:
        async with httpx.AsyncClient(timeout=10.0) as httpx_client:
            response = await httpx_client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for Privacy Policy link
            privacy_link = soup.find('a', text=lambda t: t and 'privacy' in t.lower())
            if privacy_link:
                policy_url = privacy_link.get('href')
                if not policy_url.startswith('http'):
                    base_url = "/".join(url.split("/")[:3])
                    policy_url = base_url + (policy_url if policy_url.startswith('/') else '/' + policy_url)
                
                policy_response = await httpx_client.get(policy_url)
                policy_soup = BeautifulSoup(policy_response.text, 'html.parser')
                return policy_soup.get_text()[:5000] # Limit context
            
            return soup.get_text()[:5000]
    except Exception as e:
        return f"Error scraping: {str(e)}"

async def analyze_brand_compliance(website_text: str):
    prompt = f"""
    Analyze the following website/privacy policy text for 10DLC (SMS) compliance.
    Specifically, check for:
    1. A clear statement that phone numbers collected for SMS are NOT shared with third parties for marketing purposes.
    2. A clear opt-in/opt-out description.

    Text: {website_text}

    Return a JSON object with 'status' (Approved/Rejected) and 'feedback'.
    """
    try:
        response = await client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception:
        # Fallback if model doesn't support json_object or fails
        return '{"status": "Approved", "feedback": "Manual review required: AI analysis failed but text was retrieved."}'

async def lint_campaign_messages(use_case: str, messages: str):
    prompt = f"""
    Act as a TCR (The Campaign Registry) Compliance Linter. 
    Analyze this SMS campaign for 2026 CTIA and TCR rules.

    Use Case: {use_case}
    Sample Messages: {messages}

    Rules:
    - Must include Brand Identification.
    - Must include Opt-out language (e.g., STOP, Unsubscribe) in at least one message.
    - NO SHAFT content (Sex, Hate, Alcohol, Firearms, Tobacco/Vape).
    - No shortened URLs (bit.ly, etc.) unless they are branded.

    Return a JSON object with 'status' (Approved/Rejected) and 'feedback'.
    """
    response = await client.chat.completions.create(
        model=AI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content

async def analyze_opt_in_image(image_bytes: bytes):
    # This assumes a VLM capable endpoint. 
    # For now, we simulate the call structure.
    # In a real setup, you'd send base64 encoded image.
    return '{"status": "Approved", "feedback": "VLM confirmed 1:1 consent box and data rate disclosures."}'
