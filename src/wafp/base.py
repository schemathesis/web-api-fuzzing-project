import abc
import inspect
import os
import pathlib
import subprocess
import time
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union

import attr
import structlog

from .constants import COMPOSE_PROJECT_NAME_PREFIX, DEFAULT_DOCKER_COMPOSE_FILENAME
from .docker import compose
from .loader import COLLECTION_ATTRIBUTE_NAME
from .utils import NOT_SET, NotSet, classproperty

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


class ComponentMeta(abc.ABCMeta):
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

    def __new__(cls, name: str, bases: Tuple[type, ...], namespace: Dict[str, Any], **kwargs: Any) -> "ComponentMeta":
        # This attribute is set to `True` unless explicitly defined.
        # It makes the loader to avoid collecting classes that serve as base classes
        namespace.setdefault(COLLECTION_ATTRIBUTE_NAME, True)
        return super().__new__(cls, name, bases, namespace, **kwargs)  # type: ignore


@attr.s()
class Component(metaclass=ComponentMeta):
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

    def get_docker_compose_filename(self) -> str:
        """Compose file name."""
        return DEFAULT_DOCKER_COMPOSE_FILENAME

    def get_environment_variables(self) -> Dict[str, str]:
        """Environment variables for docker-compose."""
        env = {}
        # PATH: When `-p` is passed to docker-compose via a subprocess call it fails to find `git` during build
        if "PATH" in os.environ:
            env["PATH"] = os.environ["PATH"]
        return env

    @property
    def compose(self) -> "Compose":
        """Namespace for docker-compose."""
        return Compose(self)


def on_error(message: str) -> Callable:
    """Log the given message when an error occurs."""

    def wrapper(method: Callable) -> Callable:
        def inner(self: "Compose", *args: Any, **kwargs: Any) -> subprocess.CompletedProcess:
            completed = method(self, *args, **kwargs)
            if completed.returncode != 0:
                self.component.logger.error(message, returncode=completed.returncode, stdout=completed.stdout)
            return completed

        return inner

    return wrapper


@attr.s()
class Compose:
    """Namespace for docker-compose API."""

    component: Component = attr.ib()

    def _get_common_kwargs(self) -> Dict[str, Any]:
        return {
            "path": str(self.component.path),
            "project": self.component.project_name,
            "file": self.component.get_docker_compose_filename(),
        }

    @on_error("Failed to execute `docker-compose up`")
    def up(self, timeout: Optional[int] = None, build: bool = False) -> subprocess.CompletedProcess:
        """Build / create / start containers for a docker-compose service."""
        command = [
            "up",
            "--no-color",
            # Besides better isolation, `docker-compose` won't expect user's input if a relevant image was manually
            # removed, e.g. via `docker rmi`
            "--renew-anon-volumes",
            "-d",
        ]
        if build:
            command.append("--build")
        return compose(
            command,
            timeout=timeout,
            env=self.component.get_environment_variables(),
            **self._get_common_kwargs(),
        )

    def run(
        self,
        service: str,
        args: List[str],
        timeout: Optional[int] = None,
        entrypoint: Union[str, NotSet] = NOT_SET,
        volumes: Optional[List[str]] = None,
    ) -> subprocess.CompletedProcess:
        """Run a single command on a service."""
        command = ["run"]
        if not isinstance(entrypoint, NotSet):
            command.extend(["--entrypoint", entrypoint])
        if volumes:
            for volume in volumes:
                command.extend(["-v", volume])
        command.append(service)
        command.extend(args)
        return compose(
            command,
            timeout=timeout,
            check=False,
            env=self.component.get_environment_variables(),
            **self._get_common_kwargs(),
        )

    @on_error("Failed to get docker-compose logs")
    def logs(self) -> subprocess.CompletedProcess:
        """Get project's logs available at the moment."""
        return compose(["logs", "--no-color", "--timestamps"], **self._get_common_kwargs())

    def log_stream(self, deadline: float, timeout: float = 0.5) -> Generator[bytes, None, None]:
        """Yield all available target logs repeatedly.

        All logs may not be immediately available after the target becomes available on its URL.
        Using `-f` is not an option, as it will require setting a timeout and unconditionally waiting for
        the output - retrying is simpler and more responsive.
        """
        streamed: List[bytes] = []
        while True:
            for line in self.logs().stdout.splitlines():
                # Lines from multiple services are not ordered
                if line not in streamed:
                    streamed.append(line)
                    yield line
            if time.time() >= deadline:
                return
            time.sleep(timeout)

    @on_error("Failed to stop docker-compose")
    def stop(self) -> subprocess.CompletedProcess:
        return compose(["stop"], **self._get_common_kwargs())

    @on_error("Failed to remove stopped containers")
    def rm(self) -> subprocess.CompletedProcess:
        return compose(
            [
                "rm",
                "--force",
                "--stop",
                "-v",
            ],
            **self._get_common_kwargs(),
        )
