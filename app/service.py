import hashlib
import ipaddress
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


def truncate_ip(ip_str: str) -> str:
    if not ip_str:
        return ""

    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.version == 4:
            network = ipaddress.ip_network(f"{ip}/24", strict=False)
            return str(network.network_address)

        elif ip.version == 6:
            network = ipaddress.ip_network(f"{ip}/48", strict=False)
            return str(network.network_address)
    except ValueError:
        return ""

    return ""
