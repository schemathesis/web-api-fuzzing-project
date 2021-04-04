import socket
from urllib.parse import urlparse


def is_available(url: str) -> bool:
    """Whether the `url` is available for connection or not."""
    parsed = urlparse(url)
    try:
        with socket.create_connection((parsed.hostname, parsed.port or 80)):
            return True
    except ConnectionError:
        return False


def unused_port() -> int:
    """Get an unused port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
