"""API to work with docker & docker-compose."""
import subprocess
import time
from typing import TYPE_CHECKING, Any, Callable, Dict, Generator, List, Optional

import attr
from packaging import version

from .constants import DEFAULT_DOCKER_COMPOSE_FILENAME, MINIMUM_DOCKER_COMPOSE_VERSION, MINIMUM_DOCKER_VERSION
from .errors import VersionError

if TYPE_CHECKING:
    from .core import BaseTarget


def on_error(message: str) -> Callable:
    """Log the given message when an error occurs."""

    def wrapper(method: Callable) -> Callable:
        def inner(self: "Compose", *args: Any, **kwargs: Any) -> bytes:
            try:
                return method(self, *args, **kwargs)
            except subprocess.CalledProcessError as exc:
                self.target.logger.error(message, returncode=exc.returncode, stdout=exc.stdout)
                raise

        return inner

    return wrapper


@attr.s()
class Compose:
    """Namespace for docker-compose API."""

    target: "BaseTarget" = attr.ib()

    def _get_common_kwargs(self) -> Dict[str, str]:
        return {
            "path": str(self.target.path),
            "project": self.target.project_name,
            "file": self.target.get_docker_compose_filename(),
        }

    @on_error("Target failed to start")
    def up(self, timeout: Optional[int] = None, build: bool = False) -> bytes:
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
            env=self.target.get_environment_variables(),
            **self._get_common_kwargs(),
        )

    @on_error("Failed to get target logs")
    def logs(self) -> bytes:
        """Get project's logs available at the moment."""
        return compose(["logs", "--no-color", "--timestamps"], **self._get_common_kwargs())

    @on_error("Failed to get target logs")
    def log_stream(self, deadline: float, timeout: float = 0.5) -> Generator[bytes, None, None]:
        """Yield all available target logs repeatedly.

        All logs may not be immediately available after the target becomes available on its URL.
        Using `-f` is not an option, as it will require setting a timeout and unconditionally waiting for
        the output - retrying is simpler and more responsive.
        """
        streamed: List[bytes] = []
        while True:
            for line in self.logs().splitlines():
                # Lines from multiple services are not ordered
                if line not in streamed:
                    streamed.append(line)
                    yield line
            if time.time() >= deadline:
                return
            time.sleep(timeout)

    @on_error("Target failed to stop")
    def stop(self) -> bytes:
        return compose(["stop"], **self._get_common_kwargs())

    @on_error("Failed to remove target")
    def rm(self) -> bytes:
        return compose(
            [
                "rm",
                "--force",
                "--stop",
                "-v",
            ],
            **self._get_common_kwargs(),
        )


def compose(
    command: List[str], *, path: str, project: str, file: str = DEFAULT_DOCKER_COMPOSE_FILENAME, **kwargs: Any
) -> bytes:
    """Run ``docker-compose`` in a subprocess."""
    return subprocess.check_output(
        [
            "docker-compose",
            "-f",
            file,
            "-p",
            project,  # Project names are prefixed to avoid clashing with existing projects
            *command,
        ],
        cwd=path,
        stderr=subprocess.STDOUT,
        bufsize=0,
        **kwargs,
    )


def docker(command: List[str]) -> bytes:
    """Run docker CLI in a subprocess."""
    return subprocess.check_output(
        [
            "docker",
            *command,
        ],
        stderr=subprocess.STDOUT,
        bufsize=0,
    )


def get_docker_version() -> version.Version:
    """Get the installed Docker version info."""
    output = subprocess.check_output(
        ["docker", "version", "--format", "{{json .Client.Version }}"],
        stderr=subprocess.DEVNULL,
    ).strip()
    return version.parse(output.strip(b'"').decode("utf8"))


def get_compose_version() -> version.Version:
    """Get the installed Docker-compose version info."""
    output = subprocess.check_output(
        ["docker-compose", "version", "--short"],
        stderr=subprocess.DEVNULL,
    )
    return version.parse(output.decode("utf8"))


def ensure_docker_version() -> None:
    """Ensure whether the host satisfies minimally required version of Docker & Docker-compose."""
    compose_version = get_compose_version()
    if compose_version < version.parse(MINIMUM_DOCKER_COMPOSE_VERSION):
        raise VersionError(
            f"Docker-compose {compose_version} is not supported. "
            f"You need to have at least {MINIMUM_DOCKER_COMPOSE_VERSION}"
        )
    docker_version = get_docker_version()
    if docker_version < version.parse(MINIMUM_DOCKER_VERSION):
        raise VersionError(
            f"Docker {compose_version} is not supported. You need to have at least {MINIMUM_DOCKER_VERSION}"
        )
