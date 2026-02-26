# 10DLC Opt-In & Consent Workflow Standards

## Objective
Evaluate the visual proof of opt-in (screenshots, web forms, paper forms) to ensure the consumer is providing clear, explicit, and informed consent to receive SMS messages, compliant with FCC regulations and CTIA guidelines.

## Verification Criteria

### 1. Clear Call-to-Action (CTA)
* The consumer must know exactly what they are signing up for. The form must clearly state that providing a phone number means opting into SMS messages.

### 2. FCC One-to-One Consent Rule (CRITICAL)
* Consent must be explicitly granted to the **specific brand** registering the campaign. 
* **Prohibited:** "Partner" or "Network" consent (e.g., "I agree to receive messages from [Brand] and its marketing partners"). The consumer cannot be forced to consent to third-party messages as a condition of service.

### 3. Mandatory Disclosures
The visual proof MUST contain the following disclaimers clearly visible near the phone number input or submit button:
* **Rate Disclaimer:** "Message and data rates may apply."
* **Frequency Disclaimer:** "Message frequency varies" OR a specific frequency (e.g., "Max 4 msgs/mo").
* **Support/Opt-Out Instructions:** "Reply HELP for help, STOP to cancel."
* **Links:** Must include visible links to the brand's Privacy Policy and Terms of Service.

### 4. Opt-In Mechanics
* **No Pre-Checked Boxes:** If a checkbox is used to gather SMS consent, it MUST be un-checked by default. The consumer must actively click it.
* **Non-Condition of Purchase:** Consent to receive promotional SMS cannot be a mandatory condition for purchasing a good or service.

### 5. CTA Text vs. Visual Proof Consistency
* **Cross-Reference:** The visual proof (screenshot) MUST logically match the steps described in the user's "Call-to-Action / Message Flow" text.
* *Example:* If the user's CTA text says "User fills out the Contact Us form on our website," but the uploaded screenshot is a picture of a paper sign-in sheet on a clipboard, this is a mismatch.
* *Rejection Protocol:* If the visual proof does not match the described CTA flow, mark as `FAILED` and state: "The uploaded opt-in proof does not match the process described in your Call-to-Action/Message Flow. Please ensure the screenshot reflects the exact form described."

## Rejection Protocol
If any standard is not met, mark the evaluation as `FAILED` and return specific remediation steps:
* *Missing Disclosures:* "Update the opt-in form to include the mandatory disclosure: 'Message and data rates may apply. Message frequency varies. Reply HELP for help, STOP to cancel.'"
* *Pre-checked box:* "Ensure the SMS consent checkbox is blank/un-checked by default. Consumers must actively opt-in."
* *Missing Links:* "Add clear links to your Terms of Service and Privacy Policy near the opt-in submission button."
* *Third-Party Consent:* "Remove language forcing users to opt-in to 'partners' or 'affiliates'. Consent must be 1-to-1 for your brand only."
