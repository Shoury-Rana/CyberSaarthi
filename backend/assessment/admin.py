from django.contrib import admin
from .models import ScanAssessment


@admin.register(ScanAssessment)
class ScanAssessmentAdmin(admin.ModelAdmin):
    list_display = ("id", "submission", "classification", "confidence", "created_at")
    list_filter = ("classification", "confidence")
