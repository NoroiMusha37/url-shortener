import hashlib
import string
from secrets import choice
from urllib.parse import urlparse, urlunparse

ALPHABET = string.ascii_letters + string.digits


def generate_short_code(length: int) -> str:
    return "".join(choice(ALPHABET) for _ in range(length))


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    return urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip("/"),
        parsed.params,
        parsed.query,
        parsed.fragment
    ))


def hash_url(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()
