from django.contrib import admin
from .models import ScamSubmission, ExtractedIndicator


@admin.register(ScamSubmission)
class ScamSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "channel", "input_type", "status", "created_at")
    list_filter = ("status", "channel", "input_type")
    readonly_fields = ("id", "created_at", "retention_expires_at", "decrypted_content")

    @admin.display(description="Decrypted Raw Content")
    def decrypted_content(self, obj):
        try:
            return obj.raw_content
        except Exception:
            return "(Decryption Error / Empty)"


@admin.register(ExtractedIndicator)
class ExtractedIndicatorAdmin(admin.ModelAdmin):
    list_display = ("id", "submission", "indicator_type")
    list_filter = ("indicator_type",)
