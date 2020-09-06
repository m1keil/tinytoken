from typing import Tuple
from urllib.parse import urlparse
from base64 import urlsafe_b64encode


def parse_uri(uri: str) -> Tuple[str, int]:
    """Parse given uri into hostname and port."""
    uri_parts = urlparse(uri)

    hostname = uri_parts.hostname
    if not hostname:
        raise ValueError("Invalid hostname")
    port = uri_parts.port or 80

    return hostname, port


def base64_without_padding(data: bytes) -> str:
    """Return url safe base64 string without padding

    See more: https://tools.ietf.org/html/rfc7636#appendix-A
    """
    return urlsafe_b64encode(data).decode("utf-8").rstrip("=")
