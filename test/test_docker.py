import pytest
from packaging import version

from wafp.constants import MINIMUM_DOCKER_COMPOSE_VERSION, MINIMUM_DOCKER_VERSION
from wafp.docker import ensure_docker_version
from wafp.errors import VersionError


def test_incompatible_docker_version(mocker):
    # When the installed docker version is not supported
    installed_version = "17.6"
    mocker.patch("wafp.docker.get_docker_version", return_value=version.parse(installed_version))
    with pytest.raises(
        VersionError,
        match=f"Docker {installed_version} is not supported. You need to have at least {MINIMUM_DOCKER_VERSION}",
    ):
        # Then an error should be risen
        ensure_docker_version()


def test_incompatible_docker_compose_version(mocker):
    # When the installed docker-compose version is not supported
    installed_version = "1.25.0"
    mocker.patch("wafp.docker.get_compose_version", return_value=version.parse(installed_version))
    with pytest.raises(
        VersionError,
        match=f"Docker-compose {installed_version} is not supported. "
        f"You need to have at least {MINIMUM_DOCKER_COMPOSE_VERSION}",
    ):
        # Then an error should be risen
        ensure_docker_version()
