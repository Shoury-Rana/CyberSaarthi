from django.urls import path
from .views import assess_scan, get_evidence, scan_detail, scans_collection

urlpatterns = [
    path("scans", scans_collection, name="scans-collection"),
    path("scans/<uuid:scan_id>", scan_detail, name="scan-detail"),
    path("scans/<uuid:scan_id>/assess", assess_scan, name="scan-assess"),
    path("scans/<uuid:scan_id>/evidence", get_evidence, name="scan-evidence"),
]