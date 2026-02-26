# 10DLC Brand & Identity Verification Standards

## Objective
Evaluate the brand's legal identity and web presence against The Campaign Registry (TCR) and CTIA standards. You must determine if the brand is legitimate, verifiable, and maintains compliant data privacy practices.

## Verification Criteria

### 1. Legal Identity
* **Legal Name & Tax ID (EIN):** The provided business name must exactly match the legal entity associated with the Tax ID/EIN. DBAs (Doing Business As) are acceptable only if explicitly mapped to the legal entity.
* **Address:** Must be a valid physical address. PO Boxes are strictly prohibited and will result in automatic rejection.

### 2. Web Presence
* **Website Status:** The provided website URL must resolve to a live, functioning website. Parked domains or "Under Construction" pages are invalid.
* **Relevance:** The website content must logically align with the brand's stated industry and the proposed messaging use case.

### 3. Privacy Policy & Terms of Service (CRITICAL)
* **Presence:** The website must have a publicly accessible Privacy Policy and Terms of Service (ToS).
* **Data Sharing Clause:** The Privacy Policy MUST explicitly state that mobile information will not be shared with third parties/affiliates for marketing/promotional purposes. 
* **Prohibited Language:** If the policy contains phrases like "we sell your data," "we share your phone number with our partners for marketing," or lacks an SMS-specific exclusion in their general sharing clause, it is non-compliant.

## Rejection Protocol
If any standard is not met, mark the evaluation as `FAILED` and return specific remediation steps:
* *PO Box found:* "Replace the PO Box with a valid physical business address."
* *Website dead:* "Provide a live, functioning website URL that represents the brand."
* *Privacy Policy non-compliant:* "Update the website's Privacy Policy to explicitly state that mobile phone numbers and SMS consent will not be shared with third parties or affiliates for marketing purposes."
