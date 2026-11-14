from datetime import UTC, datetime, timedelta
import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestScanAPI:
    def test_synchronous_scan_submission(self):
        client = APIClient()
        resp = client.post(
            "/api/v1/scans",
            {
                "raw_content": "Dear customer, your electricity bill unpaid. Power cut tonight. Call 9876543210",
                "reported_financial_loss": True,
            },
            format="json",
        )
        assert resp.status_code == 201
        data = resp.data
        assert data["status"] == "COMPLETED"
        assert data["reported_financial_loss"] is True
        assert data["classification"] in ("SUSPICIOUS", "HIGH_RISK")

    def test_deferred_n8n_enrichment_and_assessment(self):
        client = APIClient()
        create_resp = client.post(
            "/api/v1/scans",
            {
                "raw_content": "Update KYC at https://new-kyc-portal.example/login",
                "channel": "telegram",
                "requester_id": "99887766",
                "defer_assessment": True,
            },
            format="json",
        )
        assert create_resp.status_code == 201
        assert create_resp.data["status"] == "PENDING"
        scan_id = create_resp.data["scan_id"]

        # Unauthorized /assess rejected when token is missing
        unauth = client.post(f"/api/v1/scans/{scan_id}/assess", {"observations": []}, format="json")
        assert unauth.status_code == 401

        # n8n posts RDAP newly-registered domain (<30d) + PhishTank NO_MATCH
        recent_date = (datetime.now(UTC) - timedelta(days=3)).isoformat()
        assess_resp = client.post(
            f"/api/v1/scans/{scan_id}/assess",
            {
                "observations": [
                    {
                        "type": "URL",
                        "normalised_value": "https://new-kyc-portal.example/login",
                        "provider": "phishtank",
                        "outcome": "NO_MATCH",
                    },
                    {
                        "type": "DOMAIN",
                        "normalised_value": "new-kyc-portal.example",
                        "provider": "rdap",
                        "outcome": "NO_MATCH",
                        "response_reference": recent_date,
                    },
                ]
            },
            format="json",
            HTTP_X_INTERNAL_SERVICE_TOKEN="test-internal-token",
        )
        assert assess_resp.status_code == 200
        assert assess_resp.data["status"] == "COMPLETED"
        assert "TECH_NEW_DOMAIN" in assess_resp.data["rule_ids"]
        assert assess_resp.data["classification"] == "HIGH_RISK"
        assert assess_resp.data["defanged_indicators"][0]["value"].startswith("hxxps://")

    def test_phishtank_match_confirms_malicious(self):
        client = APIClient()
        r = client.post(
            "/api/v1/scans",
            {"raw_content": "Visit https://known-phish.example/login", "defer_assessment": True},
            format="json",
        )
        scan_id = r.data["scan_id"]
        resp = client.post(
            f"/api/v1/scans/{scan_id}/assess",
            {
                "observations": [
                    {
                        "type": "URL",
                        "normalised_value": "https://known-phish.example/login",
                        "provider": "phishtank",
                        "outcome": "MATCH",
                        "response_reference": "https://phishtank.com/detail/999",
                    }
                ]
            },
            format="json",
            HTTP_X_INTERNAL_SERVICE_TOKEN="test-internal-token",
        )
        assert resp.status_code == 200
        assert resp.data["classification"] == "CONFIRMED_MALICIOUS"

    def test_abuseipdb_alone_is_not_confirmed_malicious(self):
        client = APIClient()
        r = client.post(
            "/api/v1/scans",
            {"raw_content": "Check IP 185.220.101.5", "defer_assessment": True},
            format="json",
        )
        scan_id = r.data["scan_id"]
        resp = client.post(
            f"/api/v1/scans/{scan_id}/assess",
            {
                "observations": [
                    {
                        "type": "IP",
                        "normalised_value": "185.220.101.5",
                        "provider": "abuseipdb",
                        "outcome": "MATCH",
                        "response_reference": "abuse_confidence_score=95",
                    }
                ]
            },
            format="json",
            HTTP_X_INTERNAL_SERVICE_TOKEN="test-internal-token",
        )
        assert resp.status_code == 200
        assert resp.data["classification"] == "SUSPICIOUS"

    def test_telegram_history_filter(self):
        client = APIClient()
        client.post(
            "/api/v1/scans",
            {"raw_content": "User A message", "channel": "telegram", "requester_id": "111"},
            format="json",
        )
        client.post(
            "/api/v1/scans",
            {"raw_content": "User B message", "channel": "telegram", "requester_id": "222"},
            format="json",
        )
        hist_a = client.get("/api/v1/scans?requester_id=111&channel=telegram")
        assert hist_a.status_code == 200
        assert len(hist_a.data["results"]) == 1

    def test_scan_deletion(self):
        client = APIClient()
        create_resp = client.post(
            "/api/v1/scans",
            {"raw_content": "Suspicious test message"},
            format="json",
        )
        scan_id = create_resp.data["scan_id"]
        del_resp = client.delete(f"/api/v1/scans/{scan_id}")
        assert del_resp.status_code == 204
        assert client.get(f"/api/v1/scans/{scan_id}").status_code == 404