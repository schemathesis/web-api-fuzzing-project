import abc
import inspect
import os
import pathlib
import time
from typing import Any, Dict, List, Optional, Tuple, Type

import attr
import structlog

from . import sentry
from .artifacts import Artifact
from .constants import COMPOSE_PROJECT_NAME_PREFIX, DEFAULT_DOCKER_COMPOSE_FILENAME, WAIT_TARGET_READY_TIMEOUT
from .docker_api import Compose, docker
from .errors import TargetNotReady
from .metadata import Metadata
from .network import unused_port
from .retries import wait
from .utils import classproperty

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(),
        structlog.dev.ConsoleRenderer(),
    ],
)

logger = structlog.get_logger()


def generate_run_id() -> str:
    return str(int(time.time()))


COLLECTION_ATTRIBUTE_NAME = "__collect__"


class TargetMeta(abc.ABCMeta):
    """Custom loading behavior.

    A class defined with `__collect__ = False` won't be collected at all:

    .. code-block:: python

        from wafp.targets import BaseTarget

        # NOT COLLECTED
        class Base(BaseTarget):
            __collect__ = False
            ...

        # COLLECTED
        class Default(Base):
            ...
    """

    def __new__(cls, name: str, bases: Tuple[type, ...], namespace: Dict[str, Any], **kwargs: Any) -> "TargetMeta":
        # This attribute is set to `True` unless explicitly defined.
        # It makes the loader to avoid collecting classes that serve as base classes
        namespace.setdefault(COLLECTION_ATTRIBUTE_NAME, True)
        return super().__new__(cls, name, bases, namespace, **kwargs)  # type: ignore


@attr.s()
class BaseTarget(abc.ABC, metaclass=TargetMeta):
    port: int = attr.ib(factory=unused_port)
    build: bool = attr.ib(default=False)
    sentry_dsn: Optional[str] = attr.ib(default=None)
    run_id: str = attr.ib(factory=generate_run_id)
    wait_target_ready_timeout: int = WAIT_TARGET_READY_TIMEOUT

    @classproperty
    def path(self) -> pathlib.Path:
        """Path to the package directory."""
        file_path = inspect.getfile(self)  # type: ignore
        return pathlib.Path(file_path).parent

    @classproperty
    def name(self) -> str:
        """Target name.

        Corresponds to its package name.
        """
        return self.path.name

    @classproperty
    def logger(self) -> structlog.BoundLogger:
        return logger.bind(name=self.name)

    @classproperty
    def project_name(self) -> str:
        """Project name for docker-compose."""
        return f"{COMPOSE_PROJECT_NAME_PREFIX}{self.name}"

    @property
    def compose(self) -> Compose:
        """Namespace for docker-compose."""
        return Compose(self)

    def start(self) -> "TargetContext":
        """Start the target.

        It will be ready to serve requests after this method is called.
        """
        self.logger.msg("Start target")
        start = time.perf_counter()
        deadline = time.time() + self.wait_target_ready_timeout
        self.compose.up(timeout=self.wait_target_ready_timeout, build=self.build)
        base_url = self.get_base_url()
        # Wait until base URL is accessible
        wait(base_url)
        headers = {}
        # Then extract important information from logs
        # And decide from logs whether the service is ready
        for line in self.compose.log_stream(deadline=deadline):
            headers.update(self.get_headers(line))
            if self.is_ready(line):
                break
        else:
            message = "Target is not ready in time"
            self.logger.error(message, timeout=self.wait_target_ready_timeout, logs=self.compose.logs())
            raise TargetNotReady(message)

        logs = self.compose.logs()
        self.after_start(logs, headers)
        info = {
            "duration": round(time.perf_counter() - start, 2),
            "address": base_url,
            "schema": self.get_schema_location(),
        }
        if headers:
            info["headers"] = headers
        self.logger.msg("Target is ready", **info)
        return TargetContext(headers=headers)

    def stop(self) -> None:
        """Stop running target."""
        self.logger.msg("Stop target")
        self.compose.stop()

    def cleanup(self) -> None:
        """Remove target's resources."""
        self.logger.msg("Clean up")
        self.compose.rm()
        # There could be other networks, but delete only the one created by default for simplicity (for now)
        docker(["network", "rm", f"{self.project_name}_default"])

    # These methods are expected to be overridden

    @abc.abstractmethod
    def get_base_url(self) -> str:
        """Target base URL."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_schema_location(self) -> str:
        """Full URL of API schema."""
        raise NotImplementedError

    @abc.abstractmethod
    def is_ready(self, line: bytes) -> bool:
        """Detect whether the target is ready."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_metadata(self) -> Metadata:
        """Target meta information."""
        raise NotImplementedError

    def get_environment_variables(self) -> Dict[str, str]:
        """Environment variables for docker-compose."""
        env = {"PORT": str(self.port), "WAFP_RUN_ID": self.run_id}
        # PATH: When `-p` is passed to docker-compose via a subprocess call it fails to find `git` during build
        for key in ("PATH", "SENTRY_DSN"):
            if key in os.environ:
                env[key] = os.environ[key]
        if self.sentry_dsn is not None:
            env["SENTRY_DSN"] = self.sentry_dsn
        return env

    def get_headers(self, line: bytes) -> Dict[str, str]:
        """Extract headers from docker-compose output lines."""
        return {}

    def get_docker_compose_filename(self) -> str:
        """Compose file name."""
        return DEFAULT_DOCKER_COMPOSE_FILENAME

    def after_start(self, stdout: bytes, headers: Dict[str, str]) -> None:
        """Additional actions after the target is ready.

        E.g. create a user, login, etc.
        """

    def get_artifacts(
        self,
        sentry_url: Optional[str] = None,
        sentry_token: Optional[str] = None,
        sentry_organization: Optional[str] = None,
        sentry_project: Optional[str] = None,
    ) -> List[Artifact]:
        """Extract useful artifacts from fuzzing targets.

        By default it includes only target's stdout logs, but may also collect Sentry events for this run.

        It could also collect logs that are stored in containers directly.
        """
        artifacts = [Artifact.log(self.compose.logs())]
        if sentry_url and sentry_token and sentry_organization and sentry_project:
            events = sentry.list_events(sentry_url, sentry_token, sentry_organization, sentry_project, self.run_id)
            artifacts.extend(map(Artifact.sentry_event, events))
        return artifacts


@attr.s(slots=True)
class TargetContext:
    headers: Dict[str, str] = attr.ib()


Target = Type[BaseTarget]
