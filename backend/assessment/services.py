from __future__ import annotations

import logging
from datetime import UTC, datetime
from assessment.engine import (
    EXPLANATION_KEYS,
    classify,
    evaluate_social_engineering,
    evaluate_technical,
    load_rules,
)
from assessment.models import ScanAssessment
from core.crypto import hmac_digest
from indicators.models import (
    IndicatorObservation,
    ThreatIndicatorStatus,
    threat_indicators_for,
    upsert_indicator,
)
from submissions.models import WorkflowEvent

logger = logging.getLogger(__name__)

# Providers considered verified threat intelligence for CONFIRMED_MALICIOUS.
# AbuseIPDB is a reputation/technical signal only, never confirmation on its own.
RELIABLE_PROVIDERS = {"local_intel", "phishtank", "virustotal", "openphish"}
TRUSTED_CORROBORATORS = {"phishtank", "virustotal", "openphish"}


def _promote_on_match(submission, indicator, provider: str) -> None:
    """Enforce indicator promotion state machine (anti-pollution protection)."""
    if provider not in TRUSTED_CORROBORATORS:
        return

    def _transition(new_status: str, *, trusted: bool) -> None:
        previous = indicator.status
        try:
            indicator.transition_to(new_status, trusted=trusted)
        except ValueError:
            return
        WorkflowEvent.objects.create(
            scan=submission,
            event_type="indicator_transition",
            payload_summary={
                "indicator_type": indicator.indicator_type,
                "from": previous,
                "to": new_status,
                "provider": provider,
            },
        )

    if indicator.status == ThreatIndicatorStatus.REPORTED:
        _transition(ThreatIndicatorStatus.UNDER_REVIEW, trusted=False)

    if indicator.status == ThreatIndicatorStatus.UNDER_REVIEW:
        match_providers = set(
            indicator.observations.filter(outcome="MATCH")
            .values_list("provider", flat=True)
            .distinct()
        )
        if len(match_providers & TRUSTED_CORROBORATORS) >= 2:
            _transition(ThreatIndicatorStatus.CORROBORATED, trusted=True)


def record_external_observations(submission, observations: list[dict]) -> None:
    """Persist observations returned by n8n TI lookups and update indicator state."""
    for obs in observations:
        digest, _ = hmac_digest(obs["normalised_value"])
        provider = obs["provider"]
        outcome = obs["outcome"]
        indicator, _ = upsert_indicator(obs["type"], digest)
        IndicatorObservation.objects.create(
            indicator=indicator,
            provider=provider,
            outcome=outcome,
            response_reference=str(obs.get("response_reference", ""))[:500],
            error_detail=str(obs.get("error_detail", ""))[:500],
        )
        if outcome == "MATCH":
            _promote_on_match(submission, indicator, provider)

    WorkflowEvent.objects.create(
        scan=submission,
        event_type="enrichment_recorded",
        payload_summary={"count": len(observations)},
    )


def build_assessment(submission, observations: list[dict] | None = None) -> dict:
    observations = observations or []
    text = submission.raw_content
    se_evidence, se_rules = evaluate_social_engineering(text)

    domains = [
        ind.normalised_value
        for ind in submission.indicators.all()
        if ind.indicator_type == "DOMAIN"
    ]

    # Parse RDAP registration date for TECH_NEW_DOMAIN (< 30 days) weak signal
    domain_age_days: int | None = None
    for obs in observations:
        if obs.get("provider") != "rdap":
            continue
        ref = obs.get("response_reference")
        if not ref:
            continue
        try:
            registered = datetime.fromisoformat(str(ref))
        except ValueError:
            continue
        if registered.tzinfo is None:
            registered = registered.replace(tzinfo=UTC)
        age = (datetime.now(UTC) - registered).days
        domain_age_days = age if domain_age_days is None else min(domain_age_days, age)

    tech_evidence, tech_rules = evaluate_technical(
        domains, observations, domain_age_days=domain_age_days
    )

    has_match = any(o.get("outcome") == "MATCH" for o in observations)
    has_verified_match = any(
        o.get("outcome") == "MATCH" and o.get("provider") in RELIABLE_PROVIDERS
        for o in observations
    )

    categories: set[str] = set()
    if has_verified_match:
        categories.add("verified_threat_intel")
    elif has_match:
        categories.add("technical")
    if se_rules:
        categories.add("social_engineering")
    if "TECH_SUSPICIOUS_TLD" in tech_rules or "TECH_NEW_DOMAIN" in tech_rules:
        categories.add("technical_suspicious")

    has_weak = bool(
        "TECH_SUSPICIOUS_TLD" in tech_rules
        or "TECH_NEW_DOMAIN" in tech_rules
        or "TECH_PROVIDER_MATCH" in tech_rules
    )

    # Determine whether active external providers failed completely
    attempted_obs = [o for o in observations if o.get("outcome") != "UNSUPPORTED"]
    if attempted_obs:
        all_responded = any(o.get("outcome") in ("MATCH", "NO_MATCH") for o in attempted_obs)
    else:
        all_responded = True

    classification_result = classify(
        has_verified_match=has_verified_match,
        corroborating_categories=categories,
        se_rule_count=len(se_rules),
        has_weak_technical=has_weak,
        all_providers_responded=all_responded,
    )

    confidence = (
        "HIGH"
        if (has_verified_match or len(categories) >= 2)
        else ("MEDIUM" if (se_rules or has_weak) else "LOW")
    )
    ruleset = load_rules()

    return {
        "classification": classification_result,
        "technical_evidence": {"items": tech_evidence},
        "social_engineering_evidence": {"items": se_evidence},
        "confidence": confidence,
        "rule_ids": sorted(set(se_rules + tech_rules)),
        "ruleset_version": ruleset.get("version", "2.0"),
        "explanation_key": EXPLANATION_KEYS[classification_result],
    }


def store_assessment(submission, observations: list[dict] | None = None) -> ScanAssessment:
    payload = build_assessment(submission, observations)
    assessment, _ = ScanAssessment.objects.update_or_create(
        submission=submission, defaults=payload
    )
    submission.status = "COMPLETED"
    submission.save(update_fields=["status"])
    return assessment


def run_assessment(scan_id: str, observations: list[dict] | None = None) -> ScanAssessment:
    from submissions.models import ScamSubmission

    submission = ScamSubmission.objects.get(id=scan_id)
    inds = list(submission.indicators.all())
    pairs = {(i.indicator_type, bytes(i.digest)) for i in inds}
    threat_rows = threat_indicators_for(pairs)

    merged_obs = list(observations or [])
    for row in threat_rows:
        if row.status in (ThreatIndicatorStatus.CORROBORATED, ThreatIndicatorStatus.CONFIRMED):
            merged_obs.append({"provider": "local_intel", "outcome": "MATCH"})
        # Only pull historical DB observations if none were passed from current n8n run
        if observations is None:
            for o in row.observations.all():
                merged_obs.append(
                    {
                        "provider": o.provider,
                        "outcome": o.outcome,
                        "response_reference": o.response_reference or "",
                    }
                )

    return store_assessment(submission, merged_obs)