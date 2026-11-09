from __future__ import annotations

import logging
from assessment.engine import (
    EXPLANATION_KEYS,
    classify,
    evaluate_social_engineering,
    evaluate_technical,
    load_rules,
)
from assessment.models import ScanAssessment
from indicators.models import IndicatorObservation, ThreatIndicatorStatus, threat_indicators_for

logger = logging.getLogger(__name__)


def build_assessment(submission, observations: list[dict] | None = None) -> dict:
    observations = observations or []
    text = submission.raw_content
    se_evidence, se_rules = evaluate_social_engineering(text)

    domains = [
        ind.normalised_value
        for ind in submission.indicators.all()
        if ind.indicator_type == "DOMAIN"
    ]

    tech_evidence, tech_rules = evaluate_technical(domains, observations)

    has_verified_match = any(
        o.get("outcome") == "MATCH" and o.get("provider") in {"local_intel", "phishtank"}
        for o in observations
    )

    categories: set[str] = set()
    if has_verified_match:
        categories.add("verified_threat_intel")
    elif any(o.get("outcome") == "MATCH" for o in observations):
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

    classification_result = classify(
        has_verified_match=has_verified_match,
        corroborating_categories=categories,
        se_rule_count=len(se_rules),
        has_weak_technical=has_weak,
        all_providers_responded=True,
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


def run_assessment(scan_id: str) -> ScanAssessment:
    from submissions.models import ScamSubmission

    submission = ScamSubmission.objects.get(id=scan_id)
    inds = list(submission.indicators.all())
    pairs = {(i.indicator_type, bytes(i.digest)) for i in inds}
    threat_rows = threat_indicators_for(pairs)

    obs = []
    for row in threat_rows:
        if row.status in (ThreatIndicatorStatus.CORROBORATED, ThreatIndicatorStatus.CONFIRMED):
            obs.append({"provider": "local_intel", "outcome": "MATCH"})
        for o in row.observations.all():
            obs.append({"provider": o.provider, "outcome": o.outcome})

    return store_assessment(submission, obs)