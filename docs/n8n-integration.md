# n8n Integration & SOAR Workflow Blueprint

This document is the source of truth for building and verifying the n8n integration via the n8n MCP server. It defines the exact workflows, node contracts, environment variables, and error-handling behavior required to connect Telegram and external Threat Intelligence providers to the Django backend.

---

## Prerequisites & Environment Variables in n8n

Configure these environment variables (or equivalent n8n Variables/Credentials) in your n8n instance:

| Variable Name | Description | Example / Notes |
|---|---|---|
| `CYBERSATHI_API_BASE_URL` | Base URL of the running Django backend (no trailing slash) | `https://<tunnel-id>.ngrok-free.app` or `http://localhost:8000` |
| `CYBERSATHI_SERVICE_TOKEN` | Must match Django's `INTERNAL_SERVICE_TOKEN` | Sent as `X-Internal-Service-Token` header |
| `PHISHTANK_API_KEY` | Optional PhishTank app key | If empty/unset, skip HTTP call and return `UNSUPPORTED` |
| `ABUSEIPDB_API_KEY` | Optional AbuseIPDB API v2 key | If empty/unset, skip HTTP call and return `UNSUPPORTED` |

Additionally, attach a **Telegram Bot API** credential in n8n for the Telegram Trigger and Send Message/Document nodes.

> **Important Connectivity Note**: If n8n runs in the cloud/remote VPS while Django runs on a local laptop, start an HTTPS tunnel (`ngrok http 8000` or `cloudflared tunnel --url http://localhost:8000`) and set `CYBERSATHI_API_BASE_URL` to the public HTTPS tunnel URL. If n8n sends requests via ngrok free tier, add header `ngrok-skip-browser-warning: true` on HTTP Request nodes if needed.

---

## Workflow 1: `CyberSathi - Threat Enrichment`

**Purpose**: Reusable sub-workflow that enriches extracted indicators via PhishTank (`URL`), RDAP (`DOMAIN`), and AbuseIPDB (`IP`).

### Contract
* **Input**: `{ "indicators": [ { "type": "URL|DOMAIN|IP|PHONE|UPI|EMAIL", "value": "..." } ] }`
* **Output**: `{ "observations": [ { "type", "normalised_value", "provider", "outcome", "response_reference", "error_detail" } ] }`

### Node-by-Node Flow (Deadlock-Free Pattern)

1. **When Executed by Another Workflow** (`executeWorkflowTrigger`):
   * Accepts `{ indicators }` array.
2. **Has Indicators?** (`if`):
   * Check `$json.indicators && $json.indicators.length > 0`.
   * **False branch**: Return `{ "observations": [] }` immediately.
3. **Split Out Indicators** (`splitOut`):
   * Split on field `indicators` so each indicator becomes a separate item `{ type, value }`.
4. **Loop Over Items** (`splitInBatches`, `batchSize: 1`):
   * **Why**: Using `Loop Over Items` instead of a 4-way `Merge` node prevents n8n from hanging when a scan only contains 1 indicator type (e.g., URL-only or Domain-only).
   * Loop body connects to **Route by Indicator Type** (`switch` on `$json.type`):

   * **Branch 1 (`type === "URL"`) — PhishTank**:
     * Check if `$env.PHISHTANK_API_KEY` is non-empty (`if` node).
     * **If configured**: HTTP `POST https://checkurl.phishtank.com/checkurl/`
       * Body Content Type: `form-urlencoded` (`url={{ $json.value }}`, `format=json`, `app_key={{ $env.PHISHTANK_API_KEY }}`)
       * Header: `User-Agent: CyberSathi/1.0`
       * Options: `timeout: 5000`, `onError: "continueRegularOutput"`
       * Normalize:
         * `provider`: `"phishtank"`
         * `outcome`: HTTP 429 -> `"RATE_LIMITED"`; other error -> `"ERROR"`; `results.verified && results.valid` -> `"MATCH"`; else -> `"NO_MATCH"`
         * `response_reference`: `results.phish_detail_url || ""`
     * **If missing key**: Set `{ type, normalised_value: value, provider: "phishtank", outcome: "UNSUPPORTED", response_reference: "", error_detail: "no_api_key" }`.

   * **Branch 2 (`type === "DOMAIN"`) — RDAP Proxy**:
     * HTTP `GET https://rdap.org/domain/{{ $json.value }}`
     * Options: `timeout: 5000`, `onError: "continueRegularOutput"`
     * Normalize:
       * `provider`: `"rdap"`
       * `outcome`: error -> `"ERROR"`; else -> `"NO_MATCH"` (RDAP registration date is weak technical evidence, never a direct MATCH)
       * `response_reference`: extract ISO date from `(events || []).find(e => e.eventAction === "registration").eventDate || ""`

   * **Branch 3 (`type === "IP"`) — AbuseIPDB**:
     * Check if `$env.ABUSEIPDB_API_KEY` is non-empty (`if` node).
     * **If configured**: HTTP `GET https://api.abuseipdb.com/api/v2/check`
       * Query params: `ipAddress={{ $json.value }}`, `maxAgeInDays=90`
       * Headers: `Accept: application/json`, `Key: {{ $env.ABUSEIPDB_API_KEY }}`
       * Options: `timeout: 5000`, `onError: "continueRegularOutput"`
       * Normalize:
         * `provider`: `"abuseipdb"`
         * `outcome`: HTTP 429 -> `"RATE_LIMITED"`; other error -> `"ERROR"`; `(data.abuseConfidenceScore || 0) >= 50` -> `"MATCH"`; else -> `"NO_MATCH"`
         * `response_reference`: `"abuse_confidence_score=" + (data.abuseConfidenceScore || 0)`
     * **If missing key**: Set `{ type, normalised_value: value, provider: "abuseipdb", outcome: "UNSUPPORTED", response_reference: "", error_detail: "no_api_key" }`.

   * **Branch 4 (`PHONE`, `UPI`, `EMAIL`)**:
     * Set `{ type, normalised_value: value, provider: "none", outcome: "UNSUPPORTED", response_reference: "", error_detail: "" }`.

   * **Loop Back**: Connect the normalized output of ALL 4 branches back into the input of **Loop Over Items**.

5. **Collect & Return** (connected to the **Done** output of `Loop Over Items`):
   * Code node maps all items into a single JSON object `{ observations: $input.all().map(i => i.json) }`.

---

## Workflow 2: `CyberSathi - Telegram Bot`

**Purpose**: Citizen-facing Telegram interface executing scans, displaying defanged results, serving history, and sending ReportLab PDF dossiers.

### Node-by-Node Flow

1. **Telegram Trigger** (`telegramTrigger`):
   * Updates: `["message"]`.
2. **Parse Command & Input** (`code` node):
   * Extract `chat_id = $json.message.chat.id` and `text = ($json.message.text || $json.message.caption || "").trim()`.
   * If `!text`, drop execution cleanly.
   * Parse command:
     * `/start` or `/help` -> `action = "help"`
     * `/history` -> `action = "history"`
     * `/report` -> `action = "report"`, `arg = <optional scan_id>`
     * `/delete` -> `action = "delete"`, `arg = <scan_id>`
     * `/lost` -> `action = "scan"`, `reported_financial_loss = true`, `raw_content = <text after /lost>` (if empty after `/lost`, route to `help` or prompt user to include message)
     * Any other text/URL -> `action = "scan"`, `reported_financial_loss = false`, `raw_content = text`
3. **Route Action** (`switch` on `$json.action`):

   * **Case `help`**:
     * Telegram `sendMessage` to `chat_id` listing capabilities and commands (`/lost <msg>`, `/history`, `/report [id]`, `/delete <id>`, `/help`) plus helpline `1930`.

   * **Case `history`**:
     * HTTP `GET {{ $env.CYBERSATHI_API_BASE_URL }}/api/v1/scans?requester_id={{ chat_id }}&channel=telegram&limit=5`
     * Format `results` into a readable summary (Scan ID, Classification, Confidence, Date, plus `/report <scan_id>` hint).
     * Telegram `sendMessage` to `chat_id`.

   * **Case `delete`**:
     * If `arg` present: HTTP `DELETE {{ $env.CYBERSATHI_API_BASE_URL }}/api/v1/scans/{{ arg }}` (`onError: continueRegularOutput`).
     * Telegram `sendMessage` confirming deletion (or guiding `/delete <scan_id>` if `arg` was empty).

   * **Case `report`**:
     * If `arg` (scan_id) is empty: call HTTP `GET {{ $env.CYBERSATHI_API_BASE_URL }}/api/v1/scans?requester_id={{ chat_id }}&channel=telegram&limit=1` to read `results[0].scan_id`. If empty, send Telegram message `"No scans found yet. Send a suspicious message first."` and stop.
     * **Step 1 (Mint Signed URL)**: HTTP `GET {{ $env.CYBERSATHI_API_BASE_URL }}/api/v1/scans/{{ scan_id }}/report.pdf` -> returns `{ url }`.
     * **Step 2 (Download PDF Binary)**: HTTP `GET {{ $env.CYBERSATHI_API_BASE_URL }}{{ $json.url }}` with `Response Format = File` (`binaryPropertyName: "data"`).
     * **Step 3 (Send PDF)**: Telegram `sendDocument` with `chatId = chat_id`, binary property `"data"`, caption `"Cyber Fraud Evidence & Complaint Preparation Dossier (cybercrime.gov.in | Helpline: 1930)"`.

   * **Case `scan`**:
     * **Step 1 (Ingest & Extract)**: HTTP `POST {{ $env.CYBERSATHI_API_BASE_URL }}/api/v1/scans`
       * Header: `X-Internal-Service-Token: {{ $env.CYBERSATHI_SERVICE_TOKEN }}`
       * Body:
         ```json
         {
           "raw_content": "{{ $json.raw_content }}",
           "reported_financial_loss": {{ $json.reported_financial_loss }},
           "channel": "telegram",
           "requester_id": "{{ String($json.chat_id) }}",
           "defer_assessment": true
         }
         ```
     * **Step 2 (Enrich)**: Call Workflow 1 (`executeWorkflow`: `CyberSathi - Threat Enrichment`) passing `{ indicators: $json.indicators }`.
     * **Step 3 (Assess)**: HTTP `POST {{ $env.CYBERSATHI_API_BASE_URL }}/api/v1/scans/{{ scan_id }}/assess`
       * Header: `X-Internal-Service-Token: {{ $env.CYBERSATHI_SERVICE_TOKEN }}`
       * Body: `{ "observations": $json.observations }`
     * **Step 4 (Format Reply)** (`code` node):
       * Prepend `"🚨 EMERGENCY: Call National Cybercrime Helpline 1930 immediately!"` if `reported_financial_loss === true`.
       * Include `Classification`, `Confidence`, triggered `rule_ids`, and **`defanged_indicators`** (never raw URLs).
       * Include `disclaimer` if returned.
       * Include footer: `Scan ID: <scan_id>` and `Send /report <scan_id> to download your PDF Dossier`.
     * **Step 5 (Reply)**: Telegram `sendMessage` with `disable_web_page_preview: true`.

---

## Pre-Activation Verification Checklist

Before enabling workflows in production/demo:
1. Test **Workflow 1 (`CyberSathi - Threat Enrichment`)** with:
   * Empty array `{"indicators": []}` -> returns `{"observations": []}`.
   * URL-only `{"indicators": [{"type": "URL", "value": "https://example.com"}]}` -> completes without hanging.
   * Domain-only `{"indicators": [{"type": "DOMAIN", "value": "example.com"}]}` -> returns RDAP `registration` date in `response_reference`.
   * Phone/UPI-only -> returns `UNSUPPORTED` cleanly.
2. Test **Workflow 2 (`CyberSathi - Telegram Bot`)** commands end-to-end: `/start`, scam text, `/lost <msg>`, `/history`, `/report`, `/delete <scan_id>`.