from __future__ import annotations

import base64
import hashlib
import hmac
from cryptography.fernet import Fernet
from django.conf import settings

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = (getattr(settings, "FIELD_ENCRYPTION_KEY", "") or "").strip()
        if not key:
            key = Fernet.generate_key().decode()
        _fernet = Fernet(key.encode())
    return _fernet


def encrypt(plaintext: str) -> str:
    """Encrypt raw sensitive content at rest."""
    if not plaintext:
        return ""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt raw content. Returns empty string if missing."""
    if not ciphertext:
        return ""
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except Exception:
        return ""


def hmac_digest(value: str, key_version: str | None = None) -> tuple[bytes, str]:
    """Calculate HMAC-SHA256 digest to protect low-entropy identifiers."""
    key_b64 = (getattr(settings, "IDENTIFIER_HMAC_KEY", "") or "").strip()
    version = key_version or getattr(settings, "IDENTIFIER_HMAC_KEY_ID", "v1")
    if not key_b64:
        key = b"dev-key-change-immediately"
    else:
        try:
            key = base64.b64decode(key_b64)
        except Exception:
            key = key_b64.encode()
    digest = hmac.new(key, value.encode("utf-8"), hashlib.sha256).digest()
    return digest, version