BRAND_SECTION_ANALYSIS_PROMPT = """
Act as a 10DLC Compliance Auditor. Analyze the following SECTION of a website's Privacy Policy.

Guidelines for this section:
1. Look for clauses regarding Mobile/SMS data sharing.
2. If you find a non-compliant or "Red Flag" clause (e.g., "we share data with partners"), you MUST QUOTE IT VERBATIM in your summary.
3. Note if it explicitly states that mobile information will NOT be shared with third parties/affiliates for marketing/promotional purposes.
4. If a required 10DLC clause is MISSING entirely, note "MISSING: [Name of required clause]".

SECTION TEXT:
{section_text}

Provide a concise summary of compliance findings for ONLY this section. Quote any problematic text exactly as it appears.
"""

BRAND_SYNTHESIS_PROMPT = """
Act as a Senior 10DLC Compliance Officer. You have analyzed a Privacy Policy in multiple sections. 
Below are the compiled findings from those sections, along with the Brand Identity Guidelines.

BRAND IDENTITY GUIDELINES:
{guidelines}

COMPILED SECTION FINDINGS:
{compiled_findings}

Based on these findings, provide a final 10DLC compliance judgement.

CRITICAL INSTRUCTION for "recommended_changes":
- Each recommendation must follow the format: "[Original Text From Policy] => [New Compliant Text]".
- The "[Original Text From Policy]" MUST be a verbatim quote or specific identifiable snippet found in the COMPILED SECTION FINDINGS. 
- Do NOT use placeholder or example text for the "a" side of the "a => b".
- If a required clause is missing entirely, use "Missing: [Description]" for the "a" side.
- Example: ["'We share your contact info with our affiliates for marketing' => 'Mobile information will not be shared with third parties/affiliates for marketing/promotional purposes.'"]

Return ONLY a JSON object with the following keys:
- "status": "Approved" or "Rejected"
- "feedback": A concise summary of the overall compliance status.
- "recommended_changes": An array of "a => b" recommendations.

Final JSON:
"""

CAMPAIGN_LINTER_PROMPT = """
Act as a TCR (The Campaign Registry) Compliance Linter. 
Analyze this SMS campaign for 2026 CTIA and TCR rules based on these guidelines:

{guidelines}

CAMPAIGN DATA:
- Display Name: {display_name}
- Vertical: {vertical}
- Description: {description}
- CTA / Message Flow: {cta_flow}
- Sample Messages: {messages}
- Content Attributes: {attributes}

STRICT VALIDATION RULES:
1. **Description Check**: Verify the Description explicitly states what the messages are and who the audience is. Reject if vague.
2. **CTA Flow Check**: Verify the CTA / Message Flow is a clear, step-by-step instructional path (e.g., "1. User goes to site..."). Reject if it lacks a specific path.
3. **Attribute Cross-Check**:
   - If 'Embedded Link' is YES, at least one sample message MUST contain a URL.
   - If 'Embedded Phone Number' is YES, at least one sample message MUST contain a phone number.
4. **High-Risk Vertical/Attribute Check**: If 'Direct Lending', 'Affiliate Marketing', or 'Age-Gated Content' is YES, the status MUST be 'Rejected' with feedback that it requires manual human review due to high-risk content.

Return ONLY a JSON object with 'status' (Approved/Rejected) and 'feedback'.
Example: {{"status": "Approved", "feedback": "Criteria met."}}
"""

VISION_OPT_IN_PROMPT = """
Act as a 10DLC Opt-In Compliance Auditor. Analyze the provided screenshot of the opt-in flow.

DESCRIBED CTA FLOW:
{cta_flow}

COMPLIANCE GUIDELINES:
{guidelines}

TASKS:
1. **Consistency Check**: Does the visual proof (screenshot) logically match the step-by-step process described in the CTA Flow? 
2. **Mandatory Disclosures**: Verify the presence of:
   - "Message and data rates may apply."
   - "Message frequency varies."
   - "Reply HELP for help, STOP to cancel."
   - Links to Privacy Policy and Terms of Service.
3. **One-to-One Consent**: Ensure consent is granted specifically to the brand, not "partners".

If the image does not logically match the described CTA flow, return "status": "Rejected" and "feedback": "Visual proof does not match the described Call-to-Action flow."

Return ONLY a JSON object with 'status' (Approved/Rejected) and 'feedback'.
"""

WEB_FORM_OPT_IN_PROMPT = """
Act as a 10DLC Opt-In Compliance Auditor. Analyze the following text/HTML scraped from an opt-in web page.

DESCRIBED CTA FLOW:
{cta_flow}

SCRAPED CONTENT:
{scraped_text}

COMPLIANCE GUIDELINES:
{guidelines}

TASKS:
1. **Flow Verification**: Does the scraped page content logically support the step-by-step process described in the CTA Flow? (e.g., if they say "fill out contact form", does the page look like a contact form?)
2. **Mandatory Disclosures**: Check the text for:
   - Brand Name identification.
   - "Message and data rates may apply."
   - "Message frequency varies."
   - "Reply HELP for help, STOP to cancel."
   - Presence of links to Privacy Policy and Terms of Service.
3. **Explicit Consent**: Ensure there is language indicating a checkbox or explicit action for SMS consent.

If the page content does not match the described flow or lacks mandatory disclosures, return "status": "Rejected" and provide specific guidance on what text or elements are missing.

Return ONLY a JSON object with 'status' (Approved/Rejected) and 'feedback'.
"""

CTA_ASSIST_PROMPT = """
Act as a 10DLC Compliance Expert. Your goal is to IMPROVE and EXPAND the user's current Call-to-Action (CTA) description to ensure it passes strict TCR vetting.

BRAND NAME: {display_name}
WEBSITE: {website}
CURRENT USER INPUT:
{current_text}

INSTRUCTIONS:
1. **FOUNDATION**: Use the user's current input as the primary source of truth for the opt-in process. Do NOT replace it with a generic flow if the user provided specific steps.
2. **THE FLOW**: Rewrite the user's steps into a clear, numbered list. Be specific. If they mention a website, use the actual URL ({website}). 
3. **THE DISCLOSURE**: Append a professionally written, verbatim disclosure that would be shown to the user at the point of opt-in. This disclosure MUST include:
   - "{display_name}" (The Brand Name)
   - "Message and data rates may apply."
   - "Message frequency varies."
   - "Reply HELP for help, STOP to cancel."
   - Explicit links to the Privacy Policy and Terms of Service (use {website} as the base).
4. **COMPLIANCE CHECK**: Ensure the text explicitly states that consent is 1-to-1, intended only for {display_name}, and is NOT a condition of purchase.

OUTPUT FORMAT:
- Provide the numbered steps first.
- Provide the verbatim disclosure text clearly labeled at the end.
- Do NOT use markdown headers or bolding.
- Provide ONLY the final compliant text.
"""

SYSTEM_CHAT_PROMPT = (
    "You are a 10DLC compliance expert. Answer questions about TCR and CTIA rules."
)

USE_CASE_ASSIST_PROMPT = """
Act as a 10DLC Compliance Expert. Improve and expand the following Use Case Description.

GUIDELINES:
{guidelines}

CURRENT DESCRIPTION:
{current_text}

OUTPUT INSTRUCTIONS:
- Provide ONLY 2-5 professional sentences.
- Do NOT include headers like "Use Case Description:" or "Sample Messages:".
- Do NOT include compliance notes or explanations.
- Focus strictly on describing the purpose and nature of the SMS communications.
"""

MESSAGES_ASSIST_PROMPT = """
Act as a 10DLC Compliance Expert. Improve the following Sample SMS Messages.

GUIDELINES:
{guidelines}

CURRENT MESSAGES:
{current_text}

OUTPUT INSTRUCTIONS:
- Generate exactly 5 distinct sample messages.
- Ensure each message has Brand ID and mention of how to get HELP and how to Opt-out (STOP).
- RETURN ONLY a JSON array of 5 strings.
  Example: ["Message 1 content", "Message 2 content", "Message 3 content", "Message 4 content", "Message 5 content"]
"""

OPT_IN_ASSIST_PROMPT = """
Act as a 10DLC Compliance Expert. Generate a compliant Opt-In confirmation message.
Brand Name: {display_name}
Opt-In Keyword: {opt_in_keyword}
Opt-Out Keyword: {opt_out_keyword}
Help Keyword: {help_keyword}

Requirements:
1. Identify the Brand.
2. Confirm the subscription for the specific keyword ({opt_in_keyword}).
3. Mention "Message and data rates may apply".
4. Provide {opt_out_keyword} and {help_keyword} instructions.

Return ONLY the message text.
"""

OPT_OUT_ASSIST_PROMPT = """
Act as a 10DLC Compliance Expert. Generate a compliant Opt-Out confirmation message.
Brand Name: {display_name}
Opt-Out Keyword: {opt_out_keyword}

Requirements:
1. Identify the Brand.
2. Confirm no more messages will be sent after receiving {opt_out_keyword}.

Return ONLY the message text.
"""

HELP_ASSIST_PROMPT = """
Act as a 10DLC Compliance Expert. Generate a compliant HELP response message.
Brand Name: {display_name}
Help Keyword: {help_keyword}
Opt-Out Keyword: {opt_out_keyword}

Requirements:
1. Identify the Brand.
2. Provide support contact info (email/link).
3. Provide {opt_out_keyword} instructions.

Return ONLY the message text.
"""
