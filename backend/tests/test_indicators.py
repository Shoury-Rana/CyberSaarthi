import pytest
from core.crypto import hmac_digest
from indicators.models import ThreatIndicator, ThreatIndicatorStatus, upsert_indicator


@pytest.mark.django_db
class TestIndicators:
    def test_indicator_state_machine(self):
        digest, _ = hmac_digest("https://phishing-site.example")
        ind, created = upsert_indicator("URL", digest)
        assert created
        assert ind.status == ThreatIndicatorStatus.REPORTED

        ind.transition_to(ThreatIndicatorStatus.UNDER_REVIEW)
        assert ind.status == ThreatIndicatorStatus.UNDER_REVIEW

        # Untrusted promotion must fail
        with pytest.raises(ValueError):
            ind.transition_to(ThreatIndicatorStatus.CORROBORATED, trusted=False)