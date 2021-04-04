import pytest
from example_catalog import example


@pytest.fixture(scope="session")
def target_package():
    return example


@pytest.fixture(scope="session")
def target_path(target_package):
    return target_package.Default.path


@pytest.fixture
def target(target_package):
    instance = target_package.Default()
    yield instance
    instance.stop()
