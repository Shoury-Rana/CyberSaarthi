from __future__ import annotations

from django.conf import settings
from rest_framework import serializers


INDICATOR_TYPES = ["URL", "DOMAIN", "IP", "PHONE", "UPI", "EMAIL"]
OUTCOMES = ["MATCH", "NO_MATCH", "ERROR", "RATE_LIMITED", "UNSUPPORTED"]


class ScanCreateSerializer(serializers.Serializer):
    raw_content = serializers.CharField()
    reported_financial_loss = serializers.BooleanField(default=False)
    channel = serializers.ChoiceField(choices=["web", "telegram", "api"], default="telegram")
    requester_id = serializers.CharField(required=False, allow_blank=True, default="", max_length=128)
    defer_assessment = serializers.BooleanField(required=False, default=False)

    def validate_raw_content(self, value: str) -> str:
        limit = getattr(settings, "MAX_INPUT_CHARS", 5000)
        if len(value) > limit:
            raise serializers.ValidationError(f"Content exceeds {limit} characters limit.")
        return value


class ObservationInputSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=INDICATOR_TYPES)
    normalised_value = serializers.CharField(max_length=2048)
    provider = serializers.CharField(max_length=64)
    outcome = serializers.ChoiceField(choices=OUTCOMES)
    response_reference = serializers.CharField(required=False, allow_blank=True, default="", max_length=500)
    error_detail = serializers.CharField(required=False, allow_blank=True, default="", max_length=500)


class AssessScanSerializer(serializers.Serializer):
    observations = ObservationInputSerializer(many=True, required=False, default=list)


class IndicatorOutputSerializer(serializers.Serializer):
    type = serializers.CharField()
    value = serializers.CharField()


class ScanDetailSerializer(serializers.Serializer):
    scan_id = serializers.UUIDField()
    status = serializers.CharField()
    reported_financial_loss = serializers.BooleanField()
    created_at = serializers.DateTimeField(required=False)
    indicators = IndicatorOutputSerializer(many=True, required=False)
    defanged_indicators = IndicatorOutputSerializer(many=True, required=False)
    classification = serializers.CharField(required=False, allow_null=True)
    technical_evidence = serializers.JSONField(required=False)
    social_engineering_evidence = serializers.JSONField(required=False)
    confidence = serializers.CharField(required=False, allow_null=True)
    rule_ids = serializers.ListField(required=False)
    ruleset_version = serializers.CharField(required=False)
    explanation_key = serializers.CharField(required=False)
    disclaimer = serializers.CharField(required=False)