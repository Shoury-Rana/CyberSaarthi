import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

os.environ.setdefault("INTERNAL_SERVICE_TOKEN", "test-internal-token")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-32-chars-long!!")
os.environ.setdefault(
    "IDENTIFIER_HMAC_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
)
os.environ.setdefault(
    "FIELD_ENCRYPTION_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
)
os.environ.setdefault("DATABASE_URL", "sqlite:///db.sqlite3")


def pytest_configure(config):
    import django

    django.setup()