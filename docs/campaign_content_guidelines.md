# 10DLC Campaign Content & Use Case Standards

## Objective
Evaluate the proposed campaign use case and sample messages to ensure alignment, proper formatting, and compliance with CTIA guidelines and prohibited content (SHAFT) rules.

## Verification Criteria

### 1. Use Case Alignment
* The sample messages must directly reflect the declared Use Case (e.g., 2FA, Customer Care, Marketing).
* *Example Mismatch:* A "Customer Care" use case cannot contain sample messages offering "20% off your next purchase."

### 2. Message Formatting (The "Linter" Rules)
Every set of sample messages must demonstrate the following compliance markers:
* **Brand Identification:** At least one sample message (usually the initial one) MUST clearly identify the brand sending the message (e.g., "Hi from [Brand Name]").
* **Opt-Out Language:** At least one sample message MUST include clear opt-out instructions (e.g., "Reply STOP to cancel", "Txt STOP to opt-out").
* **Help Language (Optional but Recommended):** "Reply HELP for info".

### 3. Prohibited Content (SHAFT-C & High-Risk)
Messages MUST NOT contain or imply any of the following:
* **S.H.A.F.T.:** Sex, Hate, Alcohol, Firearms, Tobacco (including vaping).
* **C.B.D. & Cannabis:** Federally illegal substances, including CBD and marijuana, regardless of state laws.
* **High-Risk Financial:** Payday loans, short-term high-interest loans, auto loans, mortgage offers, "get rich quick" schemes, debt collection, or cryptocurrency.
* **Deceptive Marketing:** Lead generation sharing, phishing, or multi-level marketing (MLM).

### 4. Campaign Description Validation
* The "Campaign Description" must clearly explain the overall purpose of the campaign and who the target audience is.
* *Example of Good:* "This campaign is used to send appointment reminders and follow-up customer care messages to existing clients."
* *Rejection Protocol:* If the description is vague (e.g., "sending messages to customers"), mark as `FAILED` and prompt the user to add specific details about *what* the messages are and *who* receives them.

### 5. Call-to-Action (CTA) / Message Flow (CRITICAL)
The TCR and Sangoma strictly require the CTA field to be a **step-by-step instructional path** that a manual reviewer can follow to find the opt-in mechanism. It cannot be vague.
* **Format Check:** The AI must ensure the text explicitly lists the steps taken to opt-in.
* *Example of Good:* "1. User browses to our website at [URL]. 2. User clicks 'Contact Us'. 3. User fills out the form and checks the SMS consent box. 4. User submits the form."
* *Example of Bad:* "Users go to our website and sign up." (This will trigger an Error 806 rejection).
* *Rejection Protocol:* If the steps are ambiguous or missing the specific website location, mark as `FAILED` and instruct the user to write a step-by-step path detailing exactly how a consumer opts in.

### 6. Content Attribute Cross-Checking
The AI must cross-reference the selected "Campaign and Content Attributes" (Yes/No toggles) with the provided Sample Messages.
* **Embedded Links:** If "Embedded Link" is marked `Yes`, at least one sample message MUST contain a link. If a sample message contains a link, this MUST be marked `Yes`. Public URL shorteners (like bit.ly) are strictly forbidden.
* **Embedded Phone Number:** If marked `Yes`, a phone number must be in the samples. If in the samples, it must be marked `Yes`.
* **High-Risk Toggles:** If "Direct Lending", "Affiliate Marketing", or "Age-Gated Content" are marked `Yes`, the AI should flag this for immediate manual review or reject it entirely unless the brand is specifically approved for these highly restricted verticals.

## Rejection Protocol
If any standard is not met, mark the evaluation as `FAILED` and return specific remediation steps:
* *Missing Brand Name:* "Update sample messages to clearly identify your brand (e.g., include 'from [Your Brand]')."
* *Missing Opt-Out:* "Add mandatory opt-out language (e.g., 'Reply STOP to cancel') to the sample messages."
* *SHAFT Violation:* "Remove all references to [Violating Content]. This category is strictly prohibited on 10DLC networks."
