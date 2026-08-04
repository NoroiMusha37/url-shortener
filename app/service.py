import hashlib
import ipaddress
import string
from secrets import choice
from urllib.parse import urlparse, urlunparse

from fastapi import HTTPException, status

from app.logger import Logger
from app.repositories.db import DBRepository

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


async def get_link_by_short_code(short_code: str, db_repo: DBRepository):
    link = await db_repo.links.get_by_short_code(short_code)

    if not link:
        Logger.error(f"Url with short code {short_code} either expired or didn't exist")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return link
