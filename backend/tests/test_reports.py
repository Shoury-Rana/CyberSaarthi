import pytest
from rest_framework.test import APIClient
from reports.pdf import generate_pdf
from submissions.services import create_submission, start_scan_pipeline


@pytest.mark.django_db
class TestReportPDF:
    def test_pdf_generation(self):
        sub = create_submission("Your bank KYC suspended: https://bad-bank.xyz", reported_financial_loss=True)
        start_scan_pipeline(sub)
        pdf_bytes = generate_pdf(str(sub.id))
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")

    def test_signed_url_two_step_download(self):
        client = APIClient()
        sub = create_submission("Phishing alert test")
        start_scan_pipeline(sub)

        step1 = client.get(f"/api/v1/scans/{sub.id}/report.pdf")
        assert step1.status_code == 200
        download_url = step1.data["url"]
        assert "token=" in download_url

        step2 = client.get(download_url)
        assert step2.status_code == 200
        assert step2["Content-Type"] == "application/pdf"