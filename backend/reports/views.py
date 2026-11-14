from __future__ import annotations

from django.http import HttpResponse
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.request import Request
from rest_framework.response import Response

from core.problem_details import problem
from core.throttles import ReportRateThrottle
from reports.pdf import generate_pdf, signed_url, verify_token
from submissions.models import ScamSubmission


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="token",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Signed token for direct PDF download.",
        )
    ],
    responses={200: OpenApiTypes.OBJECT},
)
@api_view(["GET"])
@throttle_classes([ReportRateThrottle])
def report_pdf(request: Request, scan_id: str) -> Response | HttpResponse:
    try:
        ScamSubmission.objects.get(id=scan_id)
    except (ScamSubmission.DoesNotExist, ValueError):
        return problem("Scan not found", 404)

    token = request.query_params.get("token", "")
    if not token:
        return Response(signed_url(scan_id))

    if not verify_token(token, scan_id):
        return problem("Invalid or expired token", 403)

    pdf_bytes = generate_pdf(scan_id)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="cybersathi-{scan_id}.pdf"'
    return response