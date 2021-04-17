import sys

import pytest

from wafp.fuzzers import BaseFuzzer, loader

FUZZER_WITH_TWO_VARIANTS = """
from wafp import fuzzers

class Default(fuzzers.BaseFuzzer):
    pass

class Another(fuzzers.BaseFuzzer):
    pass
"""


@pytest.fixture
def fuzzer(request, catalog_path):
    fuzzer_name = "my_fuzzer"
    package = catalog_path / fuzzer_name
    package.mkdir()
    init = package / "__init__.py"
    init.touch()
    marker = request.node.get_closest_marker("fuzzer")
    if marker:
        text = marker.args[0]
    else:
        text = FUZZER_WITH_TWO_VARIANTS
    init.write_text(text)
    yield fuzzer_name
    sys.modules.pop(fuzzer_name, None)


def test_load_all_variants(fuzzer, catalog):
    # Loading of a fuzzer should return all defined subclasses of `BaseFuzzer`
    fuzzers = loader.load_all_variants(fuzzer, catalog=catalog)
    assert len(fuzzers) == 2
    assert all(issubclass(target, BaseFuzzer) for target in fuzzers)


@pytest.mark.usefixtures("fuzzer")
def test_get_all_variants(catalog):
    assert list(loader.get_all_variants(catalog=catalog)) == ["my_fuzzer:Another", "my_fuzzer:Default"]
