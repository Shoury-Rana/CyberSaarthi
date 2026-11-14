# Citizen CyberSathi: End-to-End Demo & Verification Scenarios

Use these test cases to verify both the **Telegram Bot + n8n SOAR pipeline** and the **Django REST API** (via `curl` or `/api/docs/`).

---

## Summary Matrix

| # | Scenario | Channel / Command | Expected Classification | Key Extracted / Triggered Signals |
|---|---|---|---|---|
| **1** | Hindi Banking KYC Scam + URL | Telegram text | `HIGH_RISK` | `SE_URGENCY_HI`, `SE_AUTHORITY_HI`, `TECH_SUSPICIOUS_TLD`, RDAP check, defanged URL |
| **2** | Electricity Cut + Indian Phone | Telegram text | `HIGH_RISK` | `SE_URGENCY_EN`, `SE_AUTHORITY_EN`, Phone `9876543210` |
| **3** | Lottery Bait + UPI VPA Handle | Telegram text | `HIGH_RISK` | `SE_FINANCIAL_BAIT_EN`, `SE_URGENCY_EN`, UPI `claimreward[@]okhdfcbank` |
| **4** | Financial Loss Escalation (`1930`) | `/lost <msg>` | `HIGH_RISK` / `SUSPICIOUS` | Emergency **1930** Helpline alert in Telegram & PDF header |
| **5** | Newly Registered Domain (`<30d`) | n8n RDAP / `/assess` | `SUSPICIOUS` / `HIGH_RISK` | `TECH_NEW_DOMAIN` from RDAP `registration` date |
| **6** | PhishTank Verified Match | n8n PhishTank / `/assess` | `CONFIRMED_MALICIOUS` | `TECH_PROVIDER_MATCH` (`HIGH` confidence) |
| **7** | AbuseIPDB Reputation Match | n8n AbuseIPDB / `/assess` | `SUSPICIOUS` (alone) / `HIGH_RISK` (+SE) | Never auto-confirmed malicious by IP score alone |
| **8** | Benign Control Message | Telegram text | `NO_KNOWN_THREAT_DETECTED` | Mandatory non-safety disclaimer displayed |
| **9** | History, PDF Dossier & Deletion | `/history`, `/report`, `/delete` | `200 OK` / `204` | Returns user's scans, sends ReportLab PDF, purges record |

---

## Telegram Bot Live Demo Walkthrough

### Test 1: `/start` & `/help`
* **Send**: `/start`
* **Expected Reply**: Welcome guide explaining how to forward suspicious SMS/URLs and listing `/lost`, `/history`, `/report`, `/delete`, and `/help`.

### Test 2: Hindi Banking / KYC Account Block SMS
* **Send**:
  ```text
  प्रिय ग्राहक, आपका SBI बैंक खाता आज रात 9:30 बजे बंद कर दिया जाएगा। तुरंत अपना केवाईसी अपडेट करें: http://sbi-kyc-verify.info
  ```
* **Expected Result**:
  * **Classification**: `HIGH_RISK` (Confidence: `HIGH`)
  * **Rules Triggered**: `SE_URGENCY_HI`, `SE_AUTHORITY_HI`, `TECH_URL_PRESENT`, `TECH_SUSPICIOUS_TLD`
  * **Defanged Output**: `hxxp://sbi-kyc-verify[.]info/` (non-clickable in Telegram!)
  * **RDAP Observation**: Queried for `sbi-kyc-verify.info` (if `< 30` days old, also triggers `TECH_NEW_DOMAIN`).

### Test 3: Electricity Disconnection + 10-Digit Mobile
* **Send**:
  ```text
  Dear Customer, Your electricity bill was unpaid and power disconnection will happen tonight. Contact officer immediately at +91 9876543210.
  ```
* **Expected Result**:
  * **Classification**: `HIGH_RISK`
  * **Rules Triggered**: `SE_URGENCY_EN`, `SE_AUTHORITY_EN`
  * **Extracted Indicator**: `PHONE: 9876543210`

### Test 4: Lottery Bait with Fraudulent UPI Handle
* **Send**:
  ```text
  Congratulations! You won a lottery prize and cashback. Act now to claim reward immediately on claimreward@okhdfcbank
  ```
* **Expected Result**:
  * **Classification**: `HIGH_RISK`
  * **Rules Triggered**: `SE_FINANCIAL_BAIT_EN`, `SE_URGENCY_EN`
  * **Extracted Indicator**: `UPI: claimreward[@]okhdfcbank`

### Test 5: Financial Loss Escalation (`/lost`)
* **Send**:
  ```text
  /lost I entered my OTP on https://fake-bank-kyc.xyz and Rs 25,000 was debited immediately.
  ```
* **Expected Result**:
  * Reply starts with bold emergency warning: **Call National Cybercrime Helpline 1930 immediately!**
  * `reported_financial_loss: true` stored on scan, activating the red alert box inside the PDF dossier.

### Test 6: Benign Control Message
* **Send**:
  ```text
  Hi Anjali, let us meet tomorrow at 4 PM to review the project slides.
  ```
* **Expected Result**:
  * **Classification**: `NO_KNOWN_THREAT_DETECTED`
  * **Rules Triggered**: None (`[]`)
  * **Mandatory Disclaimer**: *"NO_KNOWN_THREAT_DETECTED does not guarantee safety or legitimacy. Always exercise caution with unsolicited links or requests."*

### Test 7: History, PDF Dossier, and User Deletion
1. **Send**: `/history` -> Lists up to 5 recent scans for your Telegram `chat_id` (matched via keyed HMAC).
2. **Send**: `/report` (or `/report <scan_id>`) -> Bot executes two-step signed URL download and sends `cybersathi-<scan_id>.pdf` directly in chat. Verify the PDF contains the original message, defanged indicators, Section 3 External Threat Intelligence Outcomes table, rule IDs, and `cybercrime.gov.in` checklist.
3. **Send**: `/delete <scan_id>` -> Confirms deletion; subsequent `/history` no longer shows that scan.

---

## Direct Backend API Verification (`curl`)

### 1. Synchronous Direct Scan (`defer_assessment: false`)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/scans \
  -H "Content-Type: application/json" \
  -d '{"raw_content": "Electricity power disconnection tonight. Call +91 9876543210", "reported_financial_loss": true}'
```

### 2. Simulated n8n Two-Step Flow (`defer_assessment: true` -> `/assess`)
```bash
# Step A: Create deferred scan
curl -X POST http://127.0.0.1:8000/api/v1/scans \
  -H "Content-Type: application/json" \
  -H "X-Internal-Service-Token: dev-internal-service-token" \
  -d '{"raw_content": "Verify KYC at https://bad-bank-test.xyz", "channel": "telegram", "requester_id": "12345", "defer_assessment": true}'

# Step B: Post observations to /assess (replace <SCAN_ID>)
curl -X POST http://127.0.0.1:8000/api/v1/scans/<SCAN_ID>/assess \
  -H "Content-Type: application/json" \
  -H "X-Internal-Service-Token: dev-internal-service-token" \
  -d '{"observations": [{"type": "DOMAIN", "normalised_value": "bad-bank-test.xyz", "provider": "rdap", "outcome": "NO_MATCH", "response_reference": "2026-11-10T00:00:00Z"}]}'
```