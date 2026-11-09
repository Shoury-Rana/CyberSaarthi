from __future__ import annotations

from pathlib import Path
import yaml

_RULES_PATH = Path(__file__).parent / "rules.yaml"
_rules_cache: dict | None = None

SUSPICIOUS_TLDS = {".top", ".xyz", ".click", ".info", ".buzz", ".live", ".guru", ".link"}


def load_rules() -> dict:
    global _rules_cache
    if _rules_cache is None:
        with _RULES_PATH.open(encoding="utf-8") as fh:
            _rules_cache = yaml.safe_load(fh)
    return _rules_cache


def evaluate_social_engineering(text: str) -> tuple[list[dict], list[str]]:
    ruleset = load_rules()
    evidence: list[dict] = []
    matched: list[str] = []
    lowered = text.lower()

    for rule in ruleset.get("rules", []):
        if rule["category"] != "social_engineering":
            continue
        hits = [p for p in rule.get("patterns", []) if p.lower() in lowered]
        if hits:
            evidence.append({"rule_id": rule["id"], "description": rule["description"], "hits": hits})
            matched.append(rule["id"])
    return evidence, matched


def evaluate_technical(
    domains: list[str],
    observations: list[dict] | None = None,
    domain_age_days: int | None = None,
) -> tuple[list[dict], list[str]]:
    observations = observations or []
    evidence: list[dict] = []
    matched: list[str] = []

    for obs in observations:
        if obs.get("outcome") == "MATCH":
            evidence.append({"provider": obs.get("provider"), "outcome": "MATCH"})
    if any(o.get("outcome") == "MATCH" for o in observations):
        matched.append("TECH_PROVIDER_MATCH")

    if domains:
        evidence.append({"domains": domains})
        matched.append("TECH_URL_PRESENT")
        for d in domains:
            d_lower = d.lower()
            if any(d_lower.endswith(tld) for tld in SUSPICIOUS_TLDS):
                evidence.append({"domain": d, "signal": "suspicious_tld"})
                if "TECH_SUSPICIOUS_TLD" not in matched:
                    matched.append("TECH_SUSPICIOUS_TLD")

    if domain_age_days is not None and domain_age_days < 30:
        evidence.append({"domain_age_days": domain_age_days, "signal": "new_domain"})
        matched.append("TECH_NEW_DOMAIN")

    return evidence, matched


def classify(
    *,
    has_verified_match: bool,
    corroborating_categories: set[str],
    se_rule_count: int,
    has_weak_technical: bool,
    all_providers_responded: bool = True,
) -> str:
    """Deterministic classification order (first match wins).

    1. CONFIRMED_MALICIOUS: Match from verified threat intel.
    2. HIGH_RISK: >= 2 independent corroborating categories (e.g. SE + Technical).
    3. SUSPICIOUS: Any SE rule or weak technical signal.
    4. NO_KNOWN_THREAT_DETECTED: Evaluated clean with no matches.
    5. INCONCLUSIVE: Insufficient evidence.
    """
    if has_verified_match:
        return "CONFIRMED_MALICIOUS"
    if len(corroborating_categories) >= 2 or se_rule_count >= 2:
        return "HIGH_RISK"
    if se_rule_count >= 1 or has_weak_technical:
        return "SUSPICIOUS"
    if all_providers_responded:
        return "NO_KNOWN_THREAT_DETECTED"
    return "INCONCLUSIVE"


EXPLANATION_KEYS = {
    "CONFIRMED_MALICIOUS": "assessment.confirmed_malicious",
    "HIGH_RISK": "assessment.high_risk",
    "SUSPICIOUS": "assessment.suspicious",
    "NO_KNOWN_THREAT_DETECTED": "assessment.no_known_threat",
    "INCONCLUSIVE": "assessment.inconclusive",
}