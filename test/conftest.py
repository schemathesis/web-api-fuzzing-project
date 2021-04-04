import pytest

from wafp.targets.docker_api import ensure_docker_version


def pytest_configure(config):
    config.addinivalue_line("markers", "target(content): Content of `__init__.py` file for a target.")


@pytest.fixture(autouse=True, scope="session")
def check_setup():
    ensure_docker_version()
