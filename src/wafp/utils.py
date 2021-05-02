from typing import Any, Callable, Dict, List
from urllib.parse import urlparse

from .errors import InvalidHeader


class classproperty:
    def __init__(self, f: Callable):
        self.f = f

    def __get__(self, instance: Any, cls: Any) -> Any:
        return self.f(cls)


class NotSet:
    pass


NOT_SET = NotSet()


def is_url(location: str) -> bool:
    return urlparse(location).scheme != ""


def parse_headers(headers: List[str]) -> Dict[str, str]:
    """Convert headers to a dictionary.

    E.g. ["Foo: bar", "Spam: baz"] => {"Foo": "bar", "Spam": "baz"}
    """
    out = {}
    for header in headers or ():
        try:
            key, value = header.split(":", maxsplit=1)
        except ValueError:
            raise InvalidHeader(f"Headers should be in KEY:VALUE format. Got: {header}") from None
        value = value.lstrip()
        key = key.strip()
        out[key] = value
    return out
