from __future__ import annotations

import logging
import time
from django.http import HttpResponse

logger = logging.getLogger(__name__)


class CorsMiddleware:
    """Zero-dependency CORS middleware allowing seamless local development."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "OPTIONS":
            response = HttpResponse()
        else:
            response = self.get_response(request)

        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Idempotency-Key, Authorization"
        return response


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self' *; frame-ancestors 'none'; base-uri 'self'"
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class JsonLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        elapsed = time.perf_counter() - start

        logger.info(
            "api_request",
            extra={
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "latency_ms": round(elapsed * 1000, 2),
            },
        )
        return response