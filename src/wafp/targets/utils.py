from typing import Any, Callable


class classproperty:
    def __init__(self, f: Callable):
        self.f = f

    def __get__(self, instance: Any, cls: Any) -> Any:
        return self.f(cls)
