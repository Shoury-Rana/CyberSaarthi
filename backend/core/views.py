from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def healthz(request):
    return JsonResponse({"status": "ok"})


@require_GET
def readyz(request):
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False
    return JsonResponse({"database": db_ok}, status=200 if db_ok else 503)