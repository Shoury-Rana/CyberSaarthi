from assessment.engine import classify, evaluate_social_engineering


class TestClassification:
    def test_hindi_urgency_and_authority(self):
        text = "प्रिय ग्राहक, आपका बैंक खाता आज रात बंद कर दिया जाएगा। तुरंत केवाईसी अपडेट करें।"
        _, rules = evaluate_social_engineering(text)
        assert "SE_URGENCY_HI" in rules
        assert "SE_AUTHORITY_HI" in rules

    def test_classification_hierarchy(self):
        # 2 independent categories = HIGH_RISK
        assert (
            classify(
                has_verified_match=False,
                corroborating_categories={"social_engineering", "technical"},
                se_rule_count=2,
                has_weak_technical=False,
            )
            == "HIGH_RISK"
        )
        # Verified intelligence = CONFIRMED_MALICIOUS
        assert (
            classify(
                has_verified_match=True,
                corroborating_categories=set(),
                se_rule_count=0,
                has_weak_technical=False,
            )
            == "CONFIRMED_MALICIOUS"
        )