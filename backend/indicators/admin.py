from django.contrib import admin
from .models import ThreatIndicator


@admin.register(ThreatIndicator)
class ThreatIndicatorAdmin(admin.ModelAdmin):
    list_display = ("id", "indicator_type", "status", "first_seen", "last_seen")
    list_filter = ("status", "indicator_type")
