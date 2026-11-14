from __future__ import annotations

import hmac
from django.conf import settings
from django.core.cache import cache
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from assessment.models import ScanAssessment
from assessment.services import record_external_observations, run_assessment
from core.crypto import hmac_digest
from core.problem_details import problem
from core.throttles import SubmissionRateThrottle
from submissions import normalisation as norm
from submissions.models import ScamSubmission
from submissions.serializers import (
    AssessScanSerializer,
    ScanCreateSerializer,
    ScanDetailSerializer,
)
from submissions.services import create_submission, defang_value, start_scan_pipeline


def _check_service_token(request: Request) -> bool:
    expected = getattr(settings, "INTERNAL_SERVICE_TOKEN", "")
    if not expected:
        return True
    provided = request.headers.get("X-Internal-Service-Token", "")
    return hmac.compare_digest(provided, expected)


def _scan_payload(submission: ScamSubmission) -> dict:
    indicators_list = [
        {"type": ind.indicator_type, "value": ind.normalised_value}
        for ind in submission.indicators.all()
    ]
    defanged_list = [
        {"type": item["type"], "value": defang_value(item["type"], item["value"])}
        for item in indicators_list
    ]
    payload = {
        "scan_id": str(submission.id),
        "status": submission.status,
        "reported_financial_loss": submission.reported_financial_loss,
        "created_at": submission.created_at.isoformat(),
        "indicators": indicators_list,
        "defanged_indicators": defanged_list,
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


def _list_scans(request: Request) -> Response:
    requester_id = (request.query_params.get("requester_id") or "").strip()
    channel = (request.query_params.get("channel") or "telegram").strip()
    try:
        limit = min(max(int(request.query_params.get("limit", 10)), 1), 50)
    except ValueError:
        limit = 10

    if not requester_id:
        return problem("Missing requester_id query parameter", 400)

    requester_digest, _ = hmac_digest(f"{channel}:{requester_id}")
    qs = ScamSubmission.objects.filter(requester_hash=requester_digest).order_by("-created_at")[:limit]

    results = []
    for sub in qs:
        assessment = ScanAssessment.objects.filter(submission=sub).first()
        results.append(
            {
                "scan_id": str(sub.id),
                "status": sub.status,
                "classification": assessment.classification if assessment else None,
                "confidence": assessment.confidence if assessment else None,
                "reported_financial_loss": sub.reported_financial_loss,
                "created_at": sub.created_at.isoformat(),
            }
        )
    return Response({"results": results})


def _create_scan(request: Request) -> Response:
    if not _check_service_token(request):
        throttle = SubmissionRateThrottle()
        if not throttle.allow_request(request, None):
            wait = throttle.wait()
            return problem(
                "Too many requests",
                429,
                f"Rate limit exceeded. Try again in {int(wait or 60)} seconds.",
            )

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
    norm.normalise_text(data["raw_content"], max_chars=limit)

    submission = create_submission(
        raw_content=data["raw_content"],
        channel=data.get("channel", "telegram"),
        reported_financial_loss=data.get("reported_financial_loss", False),
        requester_id=data.get("requester_id", ""),
    )

    if idem_key:
        cache.set(f"idem:{idem_key}", str(submission.id), timeout=900)

    # When n8n calls with defer_assessment=True, it wants the extracted indicators first
    # so it can enrich them via PhishTank/RDAP/AbuseIPDB before calling /assess.
    if not data.get("defer_assessment", False):
        start_scan_pipeline(submission)
        submission.refresh_from_db()

    return Response(_scan_payload(submission), status=status.HTTP_201_CREATED)


@extend_schema(
    methods=["GET"],
    parameters=[
        OpenApiParameter(name="requester_id", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=True),
        OpenApiParameter(name="channel", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
        OpenApiParameter(name="limit", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False),
    ],
    responses={200: OpenApiTypes.OBJECT},
    description="List recent scans for a user (matched via keyed HMAC of requester_id).",
)
@extend_schema(
    methods=["POST"],
    request=ScanCreateSerializer,
    responses={201: ScanDetailSerializer},
    description="Submit suspicious text or URL for normalization, extraction, and assessment.",
)
@api_view(["GET", "POST"])
def scans_collection(request: Request) -> Response:
    if request.method == "GET":
        return _list_scans(request)
    return _create_scan(request)


@extend_schema(
    request=AssessScanSerializer,
    responses={200: ScanDetailSerializer},
    description="Submit external threat-intelligence observations (from n8n) and run final risk assessment.",
)
@api_view(["POST"])
def assess_scan(request: Request, scan_id: str) -> Response:
    if not _check_service_token(request):
        return problem("Unauthorized", 401, "Missing or invalid X-Internal-Service-Token header.")

    try:
        submission = ScamSubmission.objects.get(id=scan_id)
    except (ScamSubmission.DoesNotExist, ValueError):
        return problem("Scan not found", 404)

    serializer = AssessScanSerializer(data=request.data)
    if not serializer.is_valid():
        return problem("Validation failed", 400, str(serializer.errors))

    observations = serializer.validated_data["observations"]
    if observations:
        record_external_observations(submission, observations)

    run_assessment(str(submission.id), observations=observations)
    submission.refresh_from_db()
    return Response(_scan_payload(submission), status=status.HTTP_200_OK)


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