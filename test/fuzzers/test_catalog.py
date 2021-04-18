from subprocess import CalledProcessError

import pytest

from wafp.fuzzers import loader as fuzzers_loader
from wafp.targets import loader as targets_loader

from ..targets import targets_catalog


@pytest.fixture(params=fuzzers_loader.get_all_variants())
def fuzzer(request):
    instance = fuzzers_loader.by_name(request.param)()
    yield instance
    instance.stop()
    instance.cleanup()


@pytest.fixture(params=targets_loader.get_all_variants(catalog=targets_catalog.__name__))
def target(request):
    instance = targets_loader.by_name(request.param, catalog=targets_catalog.__name__)()
    yield instance
    instance.stop()
    instance.cleanup()


@pytest.mark.parametrize("headers", (None, {}, {"Foo": "Bearer bar"}))
def test_all_fuzzers(target, fuzzer, headers):
    if fuzzer.name == "swagger_conformance" and headers is not None:
        pytest.skip("Swagger-conformance doesn't support headers customization")
    # Run all implemented fuzzers against test catalog
    try:
        context = target.start()
    except CalledProcessError as exc:
        print(exc.stdout.decode("utf8", errors="replace"))
        raise
    schema = target.get_schema_location()
    base_url = target.get_base_url()
    if headers is not None:
        headers = {**context.headers, **headers}
    result = fuzzer.run(schema, base_url, headers=headers)
    if fuzzer.name == "swagger_conformance" and result.completed_process.returncode == 1:
        pytest.xfail("Swagger-conformance has a very limited spec support")
    if fuzzer.name != "cats":
        assert result.completed_process.returncode == 0
    artifacts = result.collect_artifacts()
    assert len(artifacts) > 0
