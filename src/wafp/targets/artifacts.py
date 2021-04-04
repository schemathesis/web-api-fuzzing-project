import enum
from typing import Any, Dict

import attr


class ArtifactType(enum.Enum):
    LOG = enum.auto()
    SENTRY_EVENT = enum.auto()


@attr.s(slots=True)
class Artifact:
    value: Any = attr.ib()
    type: ArtifactType = attr.ib()

    @classmethod
    def log(cls, value: bytes) -> "Artifact":
        return cls(value=value, type=ArtifactType.LOG)

    @classmethod
    def sentry_event(cls, value: Dict[str, Any]) -> "Artifact":
        return cls(value=value, type=ArtifactType.SENTRY_EVENT)
