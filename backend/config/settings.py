from __future__ import annotations

from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

for candidate in (BASE_DIR.parent / ".env", BASE_DIR / ".env"):
    if candidate.exists():
        environ.Env.read_env(str(candidate))
        break

env = environ.Env(
    DJANGO_SECRET_KEY=(str, "insecure-dev-key-change-in-production"),
    DJANGO_ALLOWED_HOSTS=(list, ["*"]),
    DATABASE_URL=(str, "sqlite:///db.sqlite3"),
    IDENTIFIER_HMAC_KEY=(str, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="),
    IDENTIFIER_HMAC_KEY_ID=(str, "v1"),
    FIELD_ENCRYPTION_KEY=(str, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="),
    INTERNAL_SERVICE_TOKEN=(str, "dev-internal-service-token"),
    MAX_INPUT_CHARS=(int, 5000),
    RETENTION_DAYS=(int, 30),
)

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "drf_spectacular",
    "core",
    "indicators",
    "assessment",
    "submissions",
    "reports",
]

MIDDLEWARE = [
    "core.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "core.middleware.SecurityHeadersMiddleware",
    "core.middleware.JsonLoggingMiddleware",
]

ROOT_URLCONF = "config.urls"
DATABASES = {"default": env.db("DATABASE_URL")}
USE_TZ = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "cybersathi-cache",
    }
}

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "submissions": "120/hour",
        "reports": "30/hour",
        "default": "120/minute",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Citizen CyberSathi API",
    "DESCRIPTION": "Citizen Phishing Early-Warning & Threat Assessment System (Telegram + n8n SOAR)",
    "VERSION": "2.1.0",
}

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

MAX_INPUT_CHARS = env("MAX_INPUT_CHARS")
RETENTION_DAYS = env("RETENTION_DAYS")
IDENTIFIER_HMAC_KEY = env("IDENTIFIER_HMAC_KEY")
IDENTIFIER_HMAC_KEY_ID = env("IDENTIFIER_HMAC_KEY_ID")
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY")
INTERNAL_SERVICE_TOKEN = env("INTERNAL_SERVICE_TOKEN")