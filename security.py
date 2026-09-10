import ipaddress
import socket
from urllib.parse import urlparse

from fastapi import HTTPException

from config import SUPPORTED_SCHEMES


def validate_url(url: str) -> str:
    if not url:
        raise HTTPException(
            status_code=400,
            detail="URL is required"
        )

    url = url.strip()

    if len(url) > 2048:
        raise HTTPException(
            status_code=400,
            detail="URL is too long"
        )

    parsed = urlparse(url)

    if parsed.scheme.lower() not in SUPPORTED_SCHEMES:
        raise HTTPException(
            status_code=400,
            detail="Only HTTP and HTTPS URLs are supported"
        )

    hostname = parsed.hostname

    if not hostname:
        raise HTTPException(
            status_code=400,
            detail="Invalid hostname"
        )

    hostname = hostname.lower().rstrip(".")

    blocked_names = {
        "localhost",
        "localhost.localdomain",
        "ip6-localhost",
        "ip6-loopback",
    }

    if hostname in blocked_names:
        raise HTTPException(
            status_code=400,
            detail="Localhost URLs are not allowed"
        )

    try:
        addresses = socket.getaddrinfo(
            hostname,
            None,
            type=socket.SOCK_STREAM
        )
    except socket.gaierror:
        raise HTTPException(
            status_code=400,
            detail="Hostname could not be resolved"
        )

    checked = set()

    for address_info in addresses:
        ip = address_info[4][0]

        if ip in checked:
            continue

        checked.add(ip)

        try:
            address = ipaddress.ip_address(ip)
        except ValueError:
            continue

        if (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_reserved
            or address.is_multicast
            or address.is_unspecified
        ):
            raise HTTPException(
                status_code=400,
                detail="Private or local network addresses are not allowed"
            )

    return url


def validate_package_name(package_name: str) -> bool:
    parts = package_name.split(".")

    if len(parts) < 2:
        return False

    for part in parts:
        if not part:
            return False

        if not (
            part[0].isalpha()
            and all(
                char.isalnum() or char == "_"
                for char in part
            )
        ):
            return False

    return True


def safe_filename(value: str) -> str:
    result = "".join(
        char if (
            char.isalnum()
            or char in "._-"
        ) else "_"
        for char in value
    )

    result = result.strip("._-")

    return result or "web2app-project"