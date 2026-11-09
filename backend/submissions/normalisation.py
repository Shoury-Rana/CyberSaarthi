from __future__ import annotations

import re
import unicodedata
from urllib.parse import urlparse

_ZERO_WIDTH = {"\u200b", "\u200c", "\u200d", "\u2060", "\ufeff", "\u00ad"}
_ALLOWED_URL_SCHEMES = {"http", "https"}

_URL_RE = re.compile(r"https?://[^\s\"'<>\]\)}]+|www\.[^\s\"'<>\]\)}]+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"(?:\+91[\s-]?|91[\s-]?|0)?[6-9](?:[\s-]?\d){9}")
_UPI_RE = re.compile(r"[\w.\-]{2,}@[a-zA-Z]{2,}")
_IP_RE = re.compile(r"(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)")
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def normalise_text(raw: str, max_chars: int = 5000) -> str:
    if len(raw) > max_chars:
        raise ValueError(f"Input exceeds maximum of {max_chars} characters")
    text = unicodedata.normalize("NFKC", raw)
    cleaned: list[str] = []
    for ch in text:
        if ch in _ZERO_WIDTH:
            continue
        if unicodedata.category(ch)[0] == "C":
            if ch in "\n\r\t":
                cleaned.append(" ")
            continue
        cleaned.append(ch)
    return re.sub(r"[ \t]+", " ", "".join(cleaned)).strip()


def detect_language(text: str) -> str:
    has_dev = bool(_DEVANAGARI_RE.search(text))
    has_latin = bool(re.search(r"[A-Za-z]", text))
    if has_dev and has_latin:
        return "mixed"
    if has_dev:
        return "hi"
    return "en"


def extract_urls(text: str) -> list[str]:
    urls: list[str] = []
    for m in _URL_RE.finditer(text):
        candidate = m.group(0).rstrip(".,;:!?)]}")
        norm = normalise_url(candidate)
        if norm:
            urls.append(norm)
    return urls


def normalise_url(raw: str) -> str | None:
    candidate = raw.strip()
    if not candidate or any(ch.isspace() for ch in candidate):
        return None
    if "://" not in candidate:
        candidate = "https://" + candidate
    try:
        parsed = urlparse(candidate)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return None

    scheme = parsed.scheme.lower()
    if scheme not in _ALLOWED_URL_SCHEMES or not hostname:
        return None
    if parsed.username or parsed.password:
        return None  # Embedded credentials rejected

    host = hostname.lower().rstrip(".")
    try:
        host = host.encode("idna").decode("ascii")
    except UnicodeError:
        return None

    if not host:
        return None

    netloc_host = f"[{host}]" if ":" in host else host
    default_port = (scheme == "https" and port == 443) or (scheme == "http" and port == 80)
    netloc = netloc_host if (port is None or default_port) else f"{netloc_host}:{port}"
    path = parsed.path or "/"
    return f"{scheme}://{netloc}{path}"


def extract_domain(url: str) -> str | None:
    try:
        return urlparse(url).hostname
    except Exception:
        return None


def extract_emails(text: str) -> list[str]:
    return [m.group(0).lower() for m in _EMAIL_RE.finditer(text)]


def extract_phones(text: str) -> list[str]:
    phones: list[str] = []
    for m in _PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[2:]
        elif len(digits) == 11 and digits.startswith("0"):
            digits = digits[1:]
        if len(digits) == 10:
            phones.append(digits)
    return phones


def extract_upi_ids(text: str) -> list[str]:
    return [
        m.group(0).lower()
        for m in _UPI_RE.finditer(text)
        if not m.group(0).lower().endswith((".com", ".in", ".org", ".net"))
    ]


def extract_ips(text: str) -> list[str]:
    return [m.group(0) for m in _IP_RE.finditer(text)]