from __future__ import annotations

import uuid
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone
from core.crypto import decrypt, encrypt


class ScanStatus(models.TextChoices):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ScamSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.CharField(max_length=16, default="telegram")
    input_type = models.CharField(max_length=16, default="text")
    raw_content_encrypted = models.TextField()
    content_hash = models.BinaryField(null=True, blank=True)
    requester_hash = models.BinaryField(null=True, blank=True, db_index=True)
    status = models.CharField(max_length=16, choices=ScanStatus.choices, default=ScanStatus.PENDING)
    reported_financial_loss = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    retention_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["status", "created_at"])]

    @property
    def raw_content(self) -> str:
        return decrypt(self.raw_content_encrypted)

    @raw_content.setter
    def raw_content(self, value: str) -> None:
        self.raw_content_encrypted = encrypt(value)
        if not self.retention_expires_at:
            retention_days = getattr(settings, "RETENTION_DAYS", 30)
            self.retention_expires_at = timezone.now() + timedelta(days=retention_days)

    def delete_content(self) -> None:
        self.raw_content_encrypted = ""
        self.save(update_fields=["raw_content_encrypted"])


class ExtractedIndicator(models.Model):
    class IndicatorType(models.TextChoices):
        URL = "URL"
        DOMAIN = "DOMAIN"
        IP = "IP"
        PHONE = "PHONE"
        UPI = "UPI"
        EMAIL = "EMAIL"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(ScamSubmission, on_delete=models.CASCADE, related_name="indicators")
    indicator_type = models.CharField(max_length=16, choices=IndicatorType.choices)
    normalised_value_encrypted = models.TextField()
    digest = models.BinaryField()
    key_version = models.CharField(max_length=32, default="v1")

    class Meta:
        unique_together = [("submission", "indicator_type", "digest")]

    @property
    def normalised_value(self) -> str:
        return decrypt(self.normalised_value_encrypted)

    @normalised_value.setter
    def normalised_value(self, value: str) -> None:
        self.normalised_value_encrypted = encrypt(value)


class WorkflowEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scan = models.ForeignKey(ScamSubmission, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=64)
    attempt = models.PositiveSmallIntegerField(default=1)
    payload_summary = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]