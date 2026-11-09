import pytest
from submissions.normalisation import (
    detect_language,
    extract_emails,
    extract_ips,
    extract_phones,
    extract_upi_ids,
    extract_urls,
    normalise_text,
    normalise_url,
)


class TestNormalisation:
    def test_nfkc_and_zero_width_stripping(self):
        text = normalise_text("Alert\u200b: Your\u200c bank\ufeff account blocked")
        assert "\u200b" not in text
        assert text == "Alert: Your bank account blocked"

    def test_url_normalisation(self):
        assert normalise_url("HTTP://SBI-KYC.INFO:80/verify") == "http://sbi-kyc.info/verify"
        assert normalise_url("https://user:pass@evil.com") is None  # embedded credentials rejected

    def test_indian_entity_extractors(self):
        sample = "Call +91 9876543210 or 09876543210, pay to fraud@okaxis, visit https://scam.in"
        assert "9876543210" in extract_phones(sample)
        assert "fraud@okaxis" in extract_upi_ids(sample)
        assert len(extract_urls(sample)) == 1

    def test_language_detection(self):
        assert detect_language("Hello Customer") == "en"
        assert detect_language("तुरंत अपडेट करें") == "hi"
        assert detect_language("KYC तुरंत अपडेट करें") == "mixed"