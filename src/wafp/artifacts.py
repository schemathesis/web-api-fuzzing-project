import enum
from typing import Any, Dict

import attr


class ArtifactType(enum.Enum):
    STDOUT = enum.auto()
    LOG_FILE = enum.auto()
    SENTRY_EVENT = enum.auto()


@attr.s(slots=True)
class Artifact:
    value: Any = attr.ib()
    type: ArtifactType = attr.ib()

    @classmethod
    def stdout(cls, value: bytes) -> "Artifact":
        return cls(value=value, type=ArtifactType.STDOUT)

    @classmethod
    def log_file(cls, value: str) -> "Artifact":
        return cls(value=value, type=ArtifactType.LOG_FILE)

    @classmethod
    def sentry_event(cls, value: Dict[str, Any]) -> "Artifact":
        return cls(value=value, type=ArtifactType.SENTRY_EVENT)
