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
        assert "SUSPICIOUS" in data["classification"] or "HIGH_RISK" in data["classification"]

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