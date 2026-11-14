from __future__ import annotations

import logging
from django.conf import settings
from django.db import transaction
from assessment.services import run_assessment
from core.crypto import encrypt, hmac_digest
from submissions.models import ExtractedIndicator, ScamSubmission, WorkflowEvent
from submissions import normalisation as norm

logger = logging.getLogger(__name__)


def defang_value(indicator_type: str, value: str) -> str:
    """Defang URLs/Domains so messaging apps never render clickable malicious links."""
    if indicator_type in ("URL", "DOMAIN"):
        return value.replace("http", "hxxp").replace(".", "[.]")
    if indicator_type in ("EMAIL", "UPI"):
        return value.replace("@", "[@]")
    return value


def create_submission(
    raw_content: str,
    channel: str = "telegram",
    reported_financial_loss: bool = False,
    requester_id: str = "",
) -> ScamSubmission:
    limit = getattr(settings, "MAX_INPUT_CHARS", 5000)
    text = norm.normalise_text(raw_content, max_chars=limit)
    content_digest, _ = hmac_digest(text)

    requester_digest = None
    clean_requester = (requester_id or "").strip()
    if clean_requester:
        requester_digest, _ = hmac_digest(f"{channel}:{clean_requester}")

    with transaction.atomic():
        submission = ScamSubmission.objects.create(
            channel=channel,
            input_type="url" if norm.extract_urls(text) else "text",
            reported_financial_loss=reported_financial_loss,
            requester_hash=requester_digest,
        )
        submission.raw_content = text
        submission.content_hash = content_digest
        submission.save()

        indicators: list[tuple[str, str]] = []
        for url in norm.extract_urls(text):
            indicators.append(("URL", url))
            domain = norm.extract_domain(url)
            if domain:
                indicators.append(("DOMAIN", domain))
        for email in norm.extract_emails(text):
            indicators.append(("EMAIL", email))
        for phone in norm.extract_phones(text):
            indicators.append(("PHONE", phone))
        for upi in norm.extract_upi_ids(text):
            indicators.append(("UPI", upi))
        for ip in norm.extract_ips(text):
            indicators.append(("IP", ip))

        seen = set()
        unique_indicators = []
        for pair in indicators:
            if pair not in seen:
                seen.add(pair)
                unique_indicators.append(pair)

        for itype, value in unique_indicators[:50]:
            digest, version = hmac_digest(value)
            ExtractedIndicator.objects.get_or_create(
                submission=submission,
                indicator_type=itype,
                digest=digest,
                defaults={
                    "key_version": version,
                    "normalised_value_encrypted": encrypt(value),
                },
            )

        WorkflowEvent.objects.create(
            scan=submission,
            event_type="submission_created",
            payload_summary={"indicator_count": len(unique_indicators)},
        )

    return submission


def start_scan_pipeline(submission: ScamSubmission):
    """Synchronous in-process evaluation pipeline."""
    return run_assessment(str(submission.id))