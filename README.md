# Citizen CyberSathi

**Citizen CyberSathi** is a bilingual (Hindi & English) cyber scam intelligence, phishing early-warning, and evidence dossier platform tailored for Indian citizens.

It combines a **Django REST Framework** cryptographic & deterministic risk engine with an **n8n SOAR (Security Orchestration, Automation, and Response)** layer that connects external Threat Intelligence providers (**PhishTank**, **RDAP**, **AbuseIPDB**) and delivers a zero-friction **Telegram Bot** interface.

---

## System Architecture

```text
Citizen (Telegram App)
   │  (Forwards SMS / URL / /lost / /report / /history)
   ▼
n8n SOAR Layer
   ├─► 1. POST /api/v1/scans (defer_assessment=true)
   │       └─► Django normalizes text, hashes requester_id, extracts URLs/UPI/Phones/IPs
   ├─► 2. Threat Enrichment Sub-Workflow (Loop Over Items, 5s timeout, fail-safe)
   │       ├─► URL    ─► PhishTank API (verified phishing check)
   │       ├─► DOMAIN ─► RDAP Proxy (https://rdap.org/domain/<host> for domain age)
   │       └─► IP     ─► AbuseIPDB API (IP reputation score >= 50)
   ├─► 3. POST /api/v1/scans/{scan_id}/assess
   │       └─► Django evaluates rules.yaml (v2.0) + TI observations -> Final Classification
   └─► 4. Replies in Telegram with Verdict, Defanged Links (hxxps://), 1930 Alert & PDF Dossier
```

---

## Key Features

1. **Telegram Bot Interface (Zero App Install)**:
   * Forward any suspicious SMS, WhatsApp message, URL, or UPI handle directly to the bot.
   * Built-in commands: `/start`, `/help`, `/lost <message>`, `/history`, `/report [scan_id]`, `/delete <scan_id>`.
2. **Bilingual Deterministic Risk Engine (`rules.yaml` v2.0)**:
   * Detects English and Hindi urgency, authority impersonation (SBI, HDFC, RBI, KYC, Electricity Bill), lottery bait, account suspension threats, and OTP/credential harvesting.
   * Never hallucinates—every verdict maps to explicit, auditable rule IDs.
3. **External Threat Intelligence via n8n SOAR**:
   * **PhishTank**: Verified URL phishing lookups (`CONFIRMED_MALICIOUS`).
   * **RDAP**: Domain registration age check (`TECH_NEW_DOMAIN` if `< 30` days old).
   * **AbuseIPDB**: IP reputation scoring (`SUSPICIOUS` alone; `HIGH_RISK` when corroborated with social engineering).
4. **Indian Entity Extraction & Defanging**:
   * Extracts 10-digit Indian mobile numbers, UPI VPA handles (`user@bank`), IPv4 addresses, emails, and canonicalized URLs (NFKC + IDNA punycode).
   * Defangs URLs/domains (`hxxps://evil[.]info`) so Telegram never creates clickable phishing links.
5. **Privacy-First Cryptography**:
   * Raw content encrypted at rest using **Fernet**.
   * Low-entropy identifiers (phones, UPI IDs) and Telegram `chat_id`s hashed via **keyed HMAC-SHA256**.
6. **1930 Emergency Escalation & ReportLab PDF Dossier**:
   * Immediately displays the **1930 National Cybercrime Helpline** banner when financial loss is reported.
   * Generates a pure-Python **ReportLab** PDF evidence dossier pre-formatted for `cybercrime.gov.in`, served via a 15-minute signed URL.

---

## Project Structure

```text
CyberSaarthi/
├── .env.example
├── .gitignore
├── README.md
├── AGENTS.md
├── DEMO_TEST_CASES.md
├── docs/
│   ├── api-contract.md
│   ├── limitations.md
│   └── n8n-integration.md
└── backend/
    ├── pyproject.toml
    ├── requirements.txt
    ├── manage.py
    ├── conftest.py
    ├── config/          # Django settings, URLs, WSGI
    ├── core/            # Fernet + HMAC crypto, CORS/CSP middleware, RFC 9457 errors, throttles
    ├── indicators/      # ThreatIndicator state machine & IndicatorObservation logs
    ├── assessment/      # rules.yaml (v2.0), deterministic engine, RDAP/TI aggregator
    ├── submissions/     # Normalisation, Indian regex extractors, REST endpoints
    ├── reports/         # ReportLab PDF generator & signed-URL download endpoints
    └── tests/           # Pytest suite (unit, API, enrichment, PDF tests)
```

---

## Local Setup & Running Guide

### 1. Environment Configuration
Copy `.env.example` to `.env` in the project root (or `backend/.env`):
```powershell
Copy-Item .env.example .env
```
Ensure `INTERNAL_SERVICE_TOKEN` matches the `CYBERSATHI_SERVICE_TOKEN` variable configured in your n8n instance.

### 2. Backend Setup (Windows PowerShell)
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
pytest tests/ -v
python manage.py runserver
```
* **API Base URL**: `http://127.0.0.1:8000`
* **Interactive Swagger Docs**: `http://127.0.0.1:8000/api/docs/`
* **Health Check**: `http://127.0.0.1:8000/healthz`

### 3. Connecting Remote n8n to Local Django
If your n8n instance is hosted remotely (cloud/VPS) while Django runs locally on port `8000`, expose your local port using an HTTPS tunnel:
```powershell
# Using ngrok:
ngrok http 8000
# OR using Cloudflare Tunnel:
cloudflared tunnel --url http://localhost:8000
```
Set n8n's `CYBERSATHI_API_BASE_URL` environment variable to the generated HTTPS URL (without a trailing slash).

### 4. n8n & Telegram Activation
Refer to `docs/n8n-integration.md` for full workflow specifications. Once workflows are active in n8n and your Telegram Bot token credential is attached, message your bot on Telegram with `/start`.