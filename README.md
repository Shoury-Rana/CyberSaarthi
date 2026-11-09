# Citizen CyberSathi

Citizen CyberSathi is a bilingual (Hindi & English) phishing intelligence and early-warning scam detection platform. It empowers citizens to analyze suspicious SMS messages, WhatsApp alerts, phishing URLs, UPI fraud attempts, and fake banking notices.

## Core Features
1. **Bilingual Heuristic Engine**: Real-time detection of urgency, authority impersonation, and lottery bait in Hindi and English.
2. **Indian Entity Extraction**: Identifies 10-digit Indian phone numbers, UPI VPA handles (`user@bank`), IPv4 addresses, and canonicalized URLs.
3. **Defanged UI**: Threat indicators are rendered safely as `hxxps://...[.]...` to prevent accidental clicks.
4. **1930 Helpline Escalation**: Immediate emergency banner when financial loss is reported.
5. **Formal Evidence Dossier**: Generates a PDF preparation report for `cybercrime.gov.in` using ReportLab (zero C-dependency requirements).
6. **Privacy-Preserving**: Encrypted at rest via Fernet; indicators hashed with keyed HMAC-SHA256.

## Running Locally

### Backend
```bash
cd backend
python -m venv .venv
# On Windows: .venv\Scripts\activate | On macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
python manage.py migrate
python manage.py runserver