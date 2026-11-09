# Citizen CyberSathi: Demonstration & Test Scenarios

This document outlines standard test cases to demonstrate and validate the **Citizen CyberSathi** scam intelligence engine. Each test covers a real-world scam vector commonly observed across India (banking fraud, electricity disconnection SMS, UPI bait, and lottery scams) as well as benign control cases.

---

## Quick Reference Summary Matrix

| # | Test Scenario | Language | Expected Classification | Key Extracted Entities | Key Triggered Rules |
|---|---|---|---|---|---|
| **1** | Hindi Banking / KYC Account Block SMS | Hindi | `HIGH_RISK` | Defanged URL, Domain | `SE_URGENCY_HI`, `SE_AUTHORITY_HI`, `TECH_SUSPICIOUS_TLD` |
| **2** | Electricity Bill Disconnection Threat | English | `HIGH_RISK` | 10-Digit Phone (`9876543210`) | `SE_URGENCY_EN`, `SE_AUTHORITY_EN` |
| **3** | Lottery / Cash Prize with UPI Handle | English | `HIGH_RISK` | UPI ID (`claim@okhdfcbank`) | `SE_FINANCIAL_BAIT_EN`, `SE_URGENCY_EN` |
| **4** | Hindi Lottery & WhatsApp Cashback Scam | Hindi | `HIGH_RISK` | Defanged URL, Phone | `SE_FINANCIAL_BAIT_HI`, `SE_URGENCY_HI` |
| **5** | Credential & OTP Harvesting with PAN/Aadhaar | English | `HIGH_RISK` | Defanged URL | `SE_CREDENTIAL_EN`, `SE_ACCOUNT_SUSPENSION_EN`, `TECH_SUSPICIOUS_TLD` |
| **6** | Financial Loss Escalation (Helpline 1930) | Any | Any + Alert Banner | Any | Emergency 1930 Banner Displayed |
| **7** | Benign / Clean Message (Control Test) | English | `NO_KNOWN_THREAT_DETECTED` | None | None (`[]`), Safe Disclaimer Shown |
| **8** | Embedded Credential Injection Defense | Any | Neutral | Cleaned host only | Invalid URL Credential Stripping |

---

## Test Scenarios

### Test Case 1: Hindi Banking & KYC Account Block SMS
* **Attack Vector**: Smishing targeting Indian public sector bank customers using urgency and fake KYC deadlines.
* **Input Text to Paste**:
  ```text
  प्रिय ग्राहक, आपका SBI बैंक खाता आज रात 9:30 बजे बंद कर दिया जाएगा। तुरंत अपना पैन कार्ड और केवाईसी अपडेट करें: http://sbi-kyc-verify.info
* **Form Settings**:
  * *Privacy Notice*: Checked
  * *Lost Money*: Unchecked
* **Expected Results**:
  * **Classification**: `HIGH_RISK`
  * **Confidence**: `HIGH`
  * **Triggered Rule IDs**:
    * `SE_URGENCY_HI` (matched `"तुरंत"`, `"बंद"`)
    * `SE_AUTHORITY_HI` (matched `"बैंक"`, `"केवाईसी"`)
    * `TECH_URL_PRESENT`
    * `TECH_SUSPICIOUS_TLD` (matched `.info`)
  * **Extracted Indicators (Defanged)**:
    * `hxxp://sbi-kyc-verify[.]info`
    * `sbi-kyc-verify[.]info`
  * **Bilingual UI**: Switch to हिन्दी to verify translated explanation and advice.

---


### Test Case 2: Electricity Power Disconnection Alert
* **Attack Vector**: High-prevalence nationwide electricity disconnection SMS targeting homeowners and small business owners.
* **Input Text to Paste**:
  ```text
  Dear Customer, Your Electricity power connection will be disconnected tonight at 9:30 PM from the power office because your previous month electricity bill was not updated. Please immediately contact our electricity officer at +91 9876543210.
  ```
* **Form Settings**:
  * *Privacy Notice*: Checked
  * *Lost Money*: Unchecked
* **Expected Results**:
  * **Classification**: `HIGH_RISK`
  * **Confidence**: `HIGH`
  * **Triggered Rule IDs**:
    * `SE_URGENCY_EN` (matched `"immediately"`)
    * `SE_AUTHORITY_EN` (matched `"electricity bill"`, `"power disconnection"`)
  * **Extracted Indicators**:
    * `9876543210` (Extracted and normalized to 10-digit Indian mobile number format)

---

### Test Case 3: Lottery Prize & Cashback with Fraudulent UPI Handle
* **Attack Vector**: Fake reward / lottery cashback prompting victim to send a small processing fee via UPI to an unauthorized handle.
* **Input Text to Paste**:
  ```text
  Congratulations! You won a lottery prize and cashback of Rs 25,000. Act now to claim reward immediately. Pay Rs 25 registration fee to claimreward@okhdfcbank
  ```
* **Form Settings**:
  * *Privacy Notice*: Checked
  * *Lost Money*: Unchecked
* **Expected Results**:
  * **Classification**: `HIGH_RISK`
  * **Confidence**: `HIGH`
  * **Triggered Rule IDs**:
    * `SE_FINANCIAL_BAIT_EN` (matched `"lottery"`, `"prize"`, `"cashback"`, `"claim reward"`)
    * `SE_URGENCY_EN` (matched `"act now"`, `"immediately"`)
  * **Extracted Indicators**:
    * `claimreward@okhdfcbank` (Categorized as `UPI`)

---

### Test Case 4: Hindi WhatsApp Lottery Scheme
* **Attack Vector**: Hindi WhatsApp forwarded message offering fake government scheme money or lottery prizes.
* **Input Text to Paste**:
  ```text
  बधाई हो! आपने जीता है 5 लाख का नकद इनाम और लॉटरी। मुफ्त उपहार प्राप्त करने के लिए जल्दी संपर्क करें: 09123456789 या देखें http://kbc-lottery-winner.xyz
  ```
* **Form Settings**:
  * *Privacy Notice*: Checked
  * *Lost Money*: Unchecked
* **Expected Results**:
  * **Classification**: `HIGH_RISK`
  * **Confidence**: `HIGH`
  * **Triggered Rule IDs**:
    * `SE_FINANCIAL_BAIT_HI` (matched `"इनाम"`, `"लॉटरी"`, `"मुफ्त"`)
    * `SE_URGENCY_HI` (matched `"जल्दी"`)
    * `TECH_URL_PRESENT`
    * `TECH_SUSPICIOUS_TLD` (matched `.xyz`)
  * **Extracted Indicators**:
    * Phone: `9123456789`
    * URL: `hxxp://kbc-lottery-winner[.]xyz`

---

### Test Case 5: Credential & OTP Harvesting with Account Suspension
* **Attack Vector**: Phishing email/SMS attempting to steal login passwords and OTP tokens through panic creation.
* **Input Text to Paste**:
  ```text
  Official notice: Your HDFC bank netbanking account suspended permanently due to suspicious activity. Enter OTP and password to reactivate your account: https://hdfc-netbanking-portal.click
  ```
* **Form Settings**:
  * *Privacy Notice*: Checked
  * *Lost Money*: Unchecked
* **Expected Results**:
  * **Classification**: `HIGH_RISK`
  * **Triggered Rule IDs**:
    * `SE_AUTHORITY_EN` (matched `"hdfc"`, `"bank"`, `"official notice"`)
    * `SE_ACCOUNT_SUSPENSION_EN` (matched `"account suspended"`, `"account blocked permanently"`, `"reactivate your account"`)
    * `SE_CREDENTIAL_EN` (matched `"enter otp"`, `"password"`)
    * `TECH_URL_PRESENT`
    * `TECH_SUSPICIOUS_TLD` (matched `.click`)
  * **Extracted Indicators**:
    * `hxxps://hdfc-netbanking-portal[.]click`

---

### Test Case 6: Emergency Financial Loss Escalation (1930 Helpline)
* **Attack Vector**: Testing immediate triage when a victim reports that money has already been stolen.
* **Input Text to Paste**:
  ```text
  I received a call claiming to be my bank manager and they deducted Rs 45,000 from my savings account.
  ```
* **Form Settings**:
  * *Privacy Notice*: Checked
  * *Lost Money*: **CHECKED** (`reported_financial_loss: true`)
* **Expected Results**:
  * **Prominent Red Alert Banner**:
    * Displays: *"EMERGENCY: Call the National Cybercrime Helpline immediately: 1930"*
    * Provides direct clickable call link: `tel:1930`
  * **Evidence Dossier (PDF)**:
    * Places a red emergency alert box at the top of the generated document instructing the victim on immediate "Golden Hour" bank account freezing.

---

### Test Case 7: Benign Control Message (No Known Threat Detected)
* **Attack Vector**: Non-fraudulent, legitimate communication to verify false-positive prevention.
* **Input Text to Paste**:
  ```text
  Hi Anjali, please find the minutes from our Monday morning project standup attached. Let us reschedule our sync to 3 PM tomorrow.
  ```
* **Form Settings**:
  * *Privacy Notice*: Checked
  * *Lost Money*: Unchecked
* **Expected Results**:
  * **Classification**: `NO_KNOWN_THREAT_DETECTED`
  * **Confidence**: `LOW`
  * **Triggered Rule IDs**: None (`[]`)
  * **Extracted Indicators**: None
  * **Mandatory Safety Disclaimer Displayed**:
    * *"NO_KNOWN_THREAT_DETECTED does not guarantee safety or legitimacy. Always exercise caution with unsolicited links or requests."*
    * *(Note: The system strictly adheres to the principle of never declaring an unknown message as "100% Safe" or "Guaranteed Legitimate".)*

---

### Test Case 8: Evidence Dossier PDF Generation & Verification
* **Goal**: Validate that official PDF dossier generation runs completely in pure Python using ReportLab without external native C-libraries.
* **Steps**:
  1. Submit any high-risk scan (e.g., Test Case 1 or Test Case 2).
  2. On the Result page, click **"Download Evidence Dossier (PDF)"** or **"View Evidence Dossier →"**.
  3. Verify the generated PDF contains:
     * Official Header: *"Cyber Fraud Evidence & Complaint Preparation Dossier"*
     * Guidance reference to **`cybercrime.gov.in`**
     * Submission Timestamp (UTC) and UUID Scan ID
     * Defanged list of extracted URLs, phone numbers, or UPI IDs
     * Triggered heuristic rule IDs list
     * Step-by-step citizen complaint filing checklist

---

### Test Case 9: Privacy Audit (User Deletion & Data Purge)
* **Goal**: Verify that citizens can purge their sensitive reports at any time.
* **Steps**:
  1. Open the top navigation and click **"Scan History"** (`/history`).
  2. Locate any previous scan in the list.
  3. Click **"Delete"**.
* **Expected Results**:
  * Frontend sends `DELETE /api/v1/scans/{scan_id}`.
  * Backend returns `204 No Content`.
  * The submission record and its encrypted raw content are permanently erased from the SQLite database.
  * Attempting to query `GET /api/v1/scans/{scan_id}` immediately returns `404 Not Found`.

---
