import subprocess
from typing import Any, List

from packaging import version

from .constants import DEFAULT_DOCKER_COMPOSE_FILENAME, MINIMUM_DOCKER_COMPOSE_VERSION, MINIMUM_DOCKER_VERSION
from .errors import VersionError


def compose(
    command: List[str],
    *,
    path: str,
    project: str,
    file: str = DEFAULT_DOCKER_COMPOSE_FILENAME,
    check: bool = True,
    **kwargs: Any,
) -> subprocess.CompletedProcess:
    """Run ``docker-compose`` in a subprocess."""
    return subprocess.run(
        [
            "docker-compose",
            "-f",
            file,
            "-p",
            project,  # Project names are prefixed to avoid clashing with existing projects
            *command,
        ],
        cwd=path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
        check=check,
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
            f"Docker {docker_version} is not supported. You need to have at least {MINIMUM_DOCKER_VERSION}"
        )
