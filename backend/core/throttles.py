from rest_framework.throttling import SimpleRateThrottle


class _IpScopedThrottle(SimpleRateThrottle):
    scope: str = "default"

    def get_cache_key(self, request, view):
        forwarded = (request.META.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip()
        ident = (
            request.META.get("HTTP_X_REAL_IP")
            or forwarded
            or request.META.get("REMOTE_ADDR", "127.0.0.1")
        )
        return self.cache_format % {"scope": self.scope, "ident": ident}


class SubmissionRateThrottle(_IpScopedThrottle):
    scope = "submissions"


class ReportRateThrottle(_IpScopedThrottle):
    scope = "reports"