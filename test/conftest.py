import pytest

from wafp.docker import ensure_docker_version

from .targets import targets_catalog


def pytest_configure(config):
    config.addinivalue_line("markers", "target(content): Content of `__init__.py` file for a target.")
    config.addinivalue_line("markers", "fuzzer(content): Content of `__init__.py` file for a fuzzer.")


@pytest.fixture(autouse=True, scope="session")
def check_setup():
    ensure_docker_version()


@pytest.fixture
def artifacts_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("artifacts")


@pytest.fixture
def catalog_path(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(tmp_path.parent)  # It should be possible to import from catalog
    return tmp_path


@pytest.fixture
def catalog(catalog_path):
    return catalog_path.name


@pytest.fixture(name="targets_catalog", scope="session")
def _targets_catalog():
    return targets_catalog


@pytest.fixture(scope="session")
def target_package():
    from .targets.targets_catalog import example_target

    return example_target


@pytest.fixture(scope="session")
def target_path(target_package):
    return target_package.Default.path


@pytest.fixture
def target(target_package):
    instance = target_package.Default()
    yield instance
    instance.stop()
    instance.cleanup()


@pytest.fixture(scope="session")
def fuzzers_catalog():
    from .fuzzers import fuzzers_catalog

    return fuzzers_catalog


@pytest.fixture(scope="session")
def fuzzer_package():
    from .fuzzers.fuzzers_catalog import example_fuzzer

    return example_fuzzer


@pytest.fixture(scope="session")
def fuzzer_path(fuzzer_package):
    return fuzzer_package.Default.path


@pytest.fixture
def fuzzer(fuzzer_package):
    instance = fuzzer_package.Default()
    yield instance
    instance.stop()
    instance.cleanup()
