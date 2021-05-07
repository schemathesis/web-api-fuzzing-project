import enum
import pathlib
import shutil
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

    def save_to(self, output_dir: pathlib.Path) -> None:
        """Save the artifact to a directory."""
        if self.type == ArtifactType.STDOUT:
            self._save_stdout(output_dir)
        if self.type == ArtifactType.LOG_FILE:
            self._save_log_file(output_dir)

    def _save_stdout(self, output_dir: pathlib.Path) -> None:
        with (output_dir / "stdout.txt").open("wb") as fd:
            fd.write(self.value)

    def _save_log_file(self, output_dir: pathlib.Path) -> None:
        source = pathlib.Path(self.value)
        if source.is_dir():
            shutil.copytree(source, output_dir, dirs_exist_ok=True)
        else:
            shutil.copy(source, output_dir)
