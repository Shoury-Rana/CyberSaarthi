from __future__ import annotations

from django.conf import settings
from django.core.cache import cache
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.request import Request
from rest_framework.response import Response

from assessment.models import ScanAssessment
from core.crypto import hmac_digest
from core.problem_details import problem
from core.throttles import SubmissionRateThrottle
from submissions import normalisation as norm
from submissions.models import ScamSubmission
from submissions.serializers import ScanCreateSerializer, ScanDetailSerializer
from submissions.services import create_submission, start_scan_pipeline


def _scan_payload(submission: ScamSubmission) -> dict:
    payload = {
        "scan_id": str(submission.id),
        "status": submission.status,
        "reported_financial_loss": submission.reported_financial_loss,
        "indicators": [
            {"type": ind.indicator_type, "value": ind.normalised_value}
            for ind in submission.indicators.all()
        ],
    }
    assessment = ScanAssessment.objects.filter(submission=submission).first()
    if assessment:
        payload.update(
            {
                "classification": assessment.classification,
                "technical_evidence": assessment.technical_evidence,
                "social_engineering_evidence": assessment.social_engineering_evidence,
                "confidence": assessment.confidence,
                "rule_ids": assessment.rule_ids,
                "ruleset_version": assessment.ruleset_version,
                "explanation_key": assessment.explanation_key,
                "disclaimer": (
                    "NO_KNOWN_THREAT_DETECTED does not guarantee safety or legitimacy. "
                    "Always exercise caution with unsolicited links or requests."
                    if assessment.classification == "NO_KNOWN_THREAT_DETECTED"
                    else ""
                ),
            }
        )
    return payload


@extend_schema(request=ScanCreateSerializer, responses={201: ScanDetailSerializer})
@api_view(["POST"])
@throttle_classes([SubmissionRateThrottle])
def create_scan(request: Request) -> Response:
    serializer = ScanCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return problem("Validation failed", 400, str(serializer.errors))

    data = serializer.validated_data
    idem_key = request.headers.get("Idempotency-Key", "")
    if idem_key:
        cached_id = cache.get(f"idem:{idem_key}")
        if cached_id:
            try:
                existing = ScamSubmission.objects.get(id=cached_id)
                return Response(_scan_payload(existing), status=status.HTTP_200_OK)
            except ScamSubmission.DoesNotExist:
                pass

    limit = getattr(settings, "MAX_INPUT_CHARS", 5000)
    text = norm.normalise_text(data["raw_content"], max_chars=limit)
    digest, _ = hmac_digest(text)

    submission = create_submission(
        raw_content=data["raw_content"],
        channel=data.get("channel", "web"),
        reported_financial_loss=data.get("reported_financial_loss", False),
    )

    if idem_key:
        cache.set(f"idem:{idem_key}", str(submission.id), timeout=900)

    # Execute synchronous scan immediately
    start_scan_pipeline(submission)
    submission.refresh_from_db()

    return Response(_scan_payload(submission), status=status.HTTP_201_CREATED)


@extend_schema(responses={200: ScanDetailSerializer, 204: OpenApiTypes.OBJECT})
@api_view(["GET", "DELETE"])
def scan_detail(request: Request, scan_id: str) -> Response:
    try:
        submission = ScamSubmission.objects.get(id=scan_id)
    except (ScamSubmission.DoesNotExist, ValueError):
        return problem("Scan not found", 404)

    if request.method == "DELETE":
        submission.delete_content()
        submission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(_scan_payload(submission))


@extend_schema(responses={200: OpenApiTypes.OBJECT})
@api_view(["GET"])
def get_evidence(request: Request, scan_id: str) -> Response:
    try:
        submission = ScamSubmission.objects.get(id=scan_id)
    except (ScamSubmission.DoesNotExist, ValueError):
        return problem("Scan not found", 404)

    indicators = [
        {"type": ind.indicator_type, "normalised_value": ind.normalised_value}
        for ind in submission.indicators.all()
    ]
    assessment = ScanAssessment.objects.filter(submission=submission).first()

    return Response(
        {
            "scan_id": str(submission.id),
            "indicators": indicators,
            "assessment": {
                "classification": assessment.classification if assessment else None,
                "rule_ids": assessment.rule_ids if assessment else [],
            },
        }
    )