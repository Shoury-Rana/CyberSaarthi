# REST API Contract (Django Backend)

All endpoints live under `/api/v1/` (plus `/healthz`, `/readyz`, and `/api/docs/`). Errors follow **RFC 9457 Problem Details** (`application/problem+json`).

---

## 1. Create Scan / Ingest Content
`POST /api/v1/scans`

* **Optional Headers**:
  * `X-Internal-Service-Token`: Bypasses per-IP rate limiting when called by n8n.
  * `Idempotency-Key`: Replays existing scan for 15 minutes (`200 OK`).
* **Request Body**:
  ```json
  {
    "raw_content": "प्रिय ग्राहक, आपका बैंक खाता बंद होगा: http://sbi-kyc.info",
    "reported_financial_loss": false,
    "channel": "telegram",
    "requester_id": "123456789",
    "defer_assessment": true
  }
  ```
* **Behavior**:
  * `defer_assessment: false` (default): Runs local heuristics immediately and returns `status: "COMPLETED"` with full assessment.
  * `defer_assessment: true` (used by n8n): Extracts and encrypts indicators, returns `status: "PENDING"` with `indicators` so n8n can perform Threat Intel lookups before calling `/assess`.
* **Response (`201 Created`)**:
  ```json
  {
    "scan_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "status": "PENDING",
    "reported_financial_loss": false,
    "created_at": "2026-11-14T14:00:00+00:00",
    "indicators": [
      { "type": "URL", "value": "http://sbi-kyc.info/" },
      { "type": "DOMAIN", "value": "sbi-kyc.info" }
    ],
    "defanged_indicators": [
      { "type": "URL", "value": "hxxp://sbi-kyc[.]info/" },
      { "type": "DOMAIN", "value": "sbi-kyc[.]info" }
    ]
  }
  ```

---

## 2. Submit External Observations & Finalize Assessment
`POST /api/v1/scans/{scan_id}/assess`

* **Required Header**: `X-Internal-Service-Token: <INTERNAL_SERVICE_TOKEN>`
* **Request Body**:
  ```json
  {
    "observations": [
      {
        "type": "URL",
        "normalised_value": "http://sbi-kyc.info/",
        "provider": "phishtank",
        "outcome": "NO_MATCH",
        "response_reference": "",
        "error_detail": ""
      },
      {
        "type": "DOMAIN",
        "normalised_value": "sbi-kyc.info",
        "provider": "rdap",
        "outcome": "NO_MATCH",
        "response_reference": "2026-11-10T00:00:00Z",
        "error_detail": ""
      }
    ]
  }
  ```
  * Valid `type`: `URL`, `DOMAIN`, `IP`, `PHONE`, `UPI`, `EMAIL`.
  * Valid `outcome`: `MATCH`, `NO_MATCH`, `ERROR`, `RATE_LIMITED`, `UNSUPPORTED`.
* **Response (`200 OK`)**:
  ```json
  {
    "scan_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "status": "COMPLETED",
    "reported_financial_loss": false,
    "created_at": "2026-11-14T14:00:00+00:00",
    "indicators": [...],
    "defanged_indicators": [...],
    "classification": "HIGH_RISK",
    "confidence": "HIGH",
    "rule_ids": ["SE_AUTHORITY_HI", "SE_URGENCY_HI", "TECH_NEW_DOMAIN", "TECH_SUSPICIOUS_TLD", "TECH_URL_PRESENT"],
    "ruleset_version": "2.0",
    "explanation_key": "assessment.high_risk",
    "disclaimer": ""
  }
  ```

---

## 3. List Scan History (Scoped by Keyed HMAC of `requester_id`)
`GET /api/v1/scans?requester_id={id}&channel=telegram&limit=10`

* **Response (`200 OK`)**:
  ```json
  {
    "results": [
      {
        "scan_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "status": "COMPLETED",
        "classification": "HIGH_RISK",
        "confidence": "HIGH",
        "reported_financial_loss": false,
        "created_at": "2026-11-14T14:00:00+00:00"
      }
    ]
  }
  ```

---

## 4. Get / Delete Single Scan
* `GET /api/v1/scans/{scan_id}` — Returns full `_scan_payload`.
* `DELETE /api/v1/scans/{scan_id}` — Purges encrypted content and deletes record (`204 No Content`).
* `GET /api/v1/scans/{scan_id}/evidence` — Returns extracted indicators and classification metadata.

---

## 5. Two-Step PDF Evidence Dossier Download
1. **Mint Signed URL**: `GET /api/v1/scans/{scan_id}/report.pdf`
   * Response (`200 OK`): `{ "url": "/api/v1/scans/{scan_id}/report.pdf?token=...", "expires_in": 900 }`
2. **Fetch PDF Bytes**: `GET /api/v1/scans/{scan_id}/report.pdf?token=...`
   * Response (`200 OK`): `Content-Type: application/pdf`, `Content-Disposition: attachment; filename="cybersathi-{scan_id}.pdf"`

---

## 6. Classification Hierarchy (First Match Wins)

| Classification | Trigger Condition | Confidence |
|---|---|---|
| `CONFIRMED_MALICIOUS` | `MATCH` from a reliable provider (`phishtank`, `virustotal`, `openphish`, `local_intel`) | `HIGH` |
| `HIGH_RISK` | `>= 2` independent corroborating categories (e.g., Social Engineering + Technical) OR `>= 2` SE rules | `HIGH` |
| `SUSPICIOUS` | `1` SE rule OR weak technical signal (`TECH_NEW_DOMAIN`, `TECH_SUSPICIOUS_TLD`, `AbuseIPDB MATCH`) | `MEDIUM` |
| `NO_KNOWN_THREAT_DETECTED` | Zero signals and at least one active provider responded cleanly (or no external lookups needed) | `LOW` |
| `INCONCLUSIVE` | Zero signals AND all attempted non-UNSUPPORTED providers returned `ERROR` / `RATE_LIMITED` | `LOW` |