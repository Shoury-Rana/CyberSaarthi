# AGENTS.md

## Repository Overview

Citizen CyberSathi is a monolithic **Django 5 / DRF + SQLite + ReportLab** backend integrated with an external **n8n SOAR** instance for Threat Intelligence enrichment (PhishTank, RDAP, AbuseIPDB) and a **Telegram Bot** user interface. There is no React frontend, Celery, or Redis in this architecture.

- `backend/` — Python 3.12+, Django 5, DRF, `drf-spectacular`, SQLite, ReportLab, PyYAML, `cryptography`, `pytest`.
- `docs/` — Integration contracts for n8n MCP (`n8n-integration.md`), REST schema (`api-contract.md`), and safety boundaries (`limitations.md`).
- `DEMO_TEST_CASES.md` — Manual functional scenarios and expected outputs.

---

## Standard Verification Commands

Run from `backend/` (with virtual environment activated):

```bash
pip install -r requirements.txt
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
pytest tests/ -v
```

---

## Configuration & Secrets

- Copy `.env.example` to `.env`. Never commit `.env` or real API tokens.
- Required backend settings (with dev fallbacks in `config/settings.py`):
  - `DJANGO_SECRET_KEY`
  - `IDENTIFIER_HMAC_KEY` & `IDENTIFIER_HMAC_KEY_ID`
  - `FIELD_ENCRYPTION_KEY`
  - `INTERNAL_SERVICE_TOKEN` (must match `CYBERSATHI_SERVICE_TOKEN` in n8n)
- `conftest.py` supplies deterministic test keys and `sqlite:///db.sqlite3` for `pytest`.
- **n8n MCP Config**: If `../opencode.json` exists in the enclosing directory, read it before calling n8n MCP tools (`get_user_preferences`, `get_instance_context`, `get_workflow_details`). Never paste n8n API keys or Telegram bot tokens into repository files.

---

## Architecture & Security Guardrails

1. **Synchronous Pipeline (No Celery / Redis)**:
   - Never reintroduce Celery, Redis, or polling queues.
   - `POST /api/v1/scans` runs synchronously:
     - `defer_assessment=false` (default): normalizes, extracts indicators, runs local `run_assessment()`, and returns `201 Created` with `status: "COMPLETED"`.
     - `defer_assessment=true` (n8n mode): saves `ScamSubmission` with `status: "PENDING"` and returns extracted indicators so n8n can enrich them via PhishTank/RDAP/AbuseIPDB, then call `POST /api/v1/scans/{scan_id}/assess` to finalize synchronously.
2. **Classification & Provider Trust Rules**:
   - Never output `"safe"` or `"legitimate"`.
   - `NO_KNOWN_THREAT_DETECTED` must always retain the non-guarantee disclaimer.
   - `CONFIRMED_MALICIOUS` is restricted strictly to `RELIABLE_PROVIDERS` (`local_intel`, `phishtank`, `virustotal`, `openphish`) in `assessment/services.py`.
   - **AbuseIPDB** is technical reputation evidence only; it must NEVER trigger `CONFIRMED_MALICIOUS` alone (`SUSPICIOUS` alone; `HIGH_RISK` if paired with Social Engineering).
   - **RDAP** registration age (`< 30` days -> `TECH_NEW_DOMAIN`) is a weak technical signal; never produces `HIGH_RISK` alone.
3. **Anti-Pollution State Machine (`indicators/models.py`, `assessment/services.py`)**:
   - Single user report -> `REPORTED`.
   - 1 trusted `MATCH` (`phishtank`, `virustotal`, `openphish`) -> `UNDER_REVIEW`.
   - 2+ distinct trusted `MATCH` providers -> `CORROBORATED`.
   - Never promote to `CONFIRMED` automatically.
4. **PII Privacy & Safe Rendering**:
   - Never fetch user-submitted URLs server-side from Django.
   - Always return `defanged_indicators` (`hxxps://...[.]...`) for display in Telegram so chat clients do not generate clickable phishing links.
   - Telegram `chat_id` is stored only as a keyed HMAC digest (`requester_hash` = `hmac("telegram:" + requester_id)`). Never store plaintext Telegram user IDs on `ScamSubmission`.
5. **ReportLab PDF Safety (`reports/pdf.py`)**:
   - All dynamic text inside ReportLab `Paragraph` blocks must pass through `_safe_pdf_text()` (`html.escape` + Latin-1 safe fallback if no TTF Unicode font is found) to avoid `ExpatError` or `UnicodeEncodeError`.
   - `GET /api/v1/scans/{scan_id}/report.pdf` without `?token=` mints `{ url, expires_in: 900 }`; only requests carrying a valid signed `?token=` receive `application/pdf` bytes.

---

## n8n MCP Integration Rules

- Detailed workflow specifications live in `docs/n8n-integration.md`.
- **Avoid 4-way `Merge` node deadlocks**: Process indicators in n8n using `Split Out` + `Loop Over Items` (`splitInBatches`, `batchSize: 1`) routing back to the loop input, rather than a multi-branch `Merge` node that hangs on incomplete branches (e.g., URL-only scans).
- Every external HTTP node (PhishTank, RDAP, AbuseIPDB) must set `timeout: 5000` and `onError: "continueRegularOutput"` so provider downtime becomes `ERROR` or `RATE_LIMITED` and never stalls a user scan.
- Before activating any workflow in n8n, verify both a text-only payload and a URL-only payload via synthetic/test execution.