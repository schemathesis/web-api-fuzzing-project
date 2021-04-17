from typing import Any, Callable
from urllib.parse import urlparse


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
