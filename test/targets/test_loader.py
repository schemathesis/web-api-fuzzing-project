import sys

import pytest

from wafp.errors import AmbiguousItemNameError
from wafp.targets import BaseTarget, loader

TARGET_WITH_ONE_VARIANT = """
from wafp import targets

class Default(targets.BaseTarget):

    def get_base_url(self) -> str:
        return f"http://0.0.0.0:{self.port}/"

    def get_schema_location(self) -> str:
        return f"http://0.0.0.0:{self.port}/spec.json"
"""


TARGET_WITH_TWO_VARIANTS = (
    TARGET_WITH_ONE_VARIANT
    + """
class Another(Default):

    def get_schema_location(self) -> str:
        return f"http://0.0.0.0:{self.port}/specv2.json"
"""
)

TARGET_WITH_BASE_TARGET = """
from wafp.targets import BaseTarget

class Default(BaseTarget):

    def get_base_url(self) -> str:
        return f"http://0.0.0.0:{self.port}/"

    def get_schema_location(self) -> str:
        return f"http://0.0.0.0:{self.port}/spec.json"
"""
TARGET_WITH_EXCLUDED_BASE_CLASS = """
from wafp.targets import BaseTarget

class Base(BaseTarget):
    __collect__ = False

    def get_base_url(self) -> str:
        return f"http://0.0.0.0:{self.port}/"

    def get_schema_location(self) -> str:
        return f"http://0.0.0.0:{self.port}/spec.json"

class Default(Base):
    pass
"""


@pytest.fixture
def target(request, catalog_path):
    target_name = "my_target"
    package = catalog_path / target_name
    package.mkdir()
    init = package / "__init__.py"
    init.touch()
    marker = request.node.get_closest_marker("target")
    if marker:
        text = marker.args[0]
    else:
        text = TARGET_WITH_TWO_VARIANTS
    init.write_text(text)
    yield target_name
    sys.modules.pop(target_name, None)


def test_load_all_variants(target, catalog):
    # Loading of a target should return all defined subclasses of `BaseTarget`
    targets = loader.load_all_variants(target, catalog=catalog)
    assert len(targets) == 2
    assert all(issubclass(target, BaseTarget) for target in targets)


def test_by_name(target, catalog):
    # When a specific variant of a target is loaded
    name = "Default"
    variant = loader.by_name(f"{target}:{name}", catalog)
    # Then the loader should load a target with exactly matching name
    assert variant.__name__ == name


@pytest.mark.parametrize("get_name", (lambda s: f"{s}:Unknown", lambda s: "unknown"))
def test_by_name_not_found(target, catalog, get_name):
    # When an unknown name is given in a custom catalog
    variant = loader.by_name(get_name(target), catalog)
    # Then nothing should be found
    assert variant is None


def test_by_name_not_found_default_catalog():
    # When an unknown name is given
    variant = loader.by_name("unknown")
    # Then nothing should be found
    assert variant is None


@pytest.mark.target(TARGET_WITH_ONE_VARIANT)
def test_by_name_default(target, catalog):
    # When the variant is not specified
    # And the target has only one variant
    variant = loader.by_name(target, catalog)
    # Then this variant should be loaded
    assert variant.__name__ == "Default"


def test_by_name_ambiguous(target, catalog):
    # When the target defines multiple variants
    # And the variant is not specified during loading
    with pytest.raises(
        AmbiguousItemNameError,
        match="`my_target` defines multiple variants, and it is not clear which one to load. "
        "You need to specify a fully qualified name. Variants: my_target:Another, my_target:Default",
    ):
        # Then it leads to an error
        loader.by_name(target, catalog)


@pytest.mark.target(TARGET_WITH_ONE_VARIANT)
def test_get_all_variants_single_target(target, catalog):
    # When only a single variant is available
    # Then only target name should be found
    assert list(loader.get_all_variants(catalog=catalog)) == [target]


def test_get_all_variants_multiple_targets(target, catalog):
    # When there are multiple variants available
    # Then only fully qualified names should be available
    assert list(loader.get_all_variants(catalog=catalog)) == [
        "my_target:Another",
        "my_target:Default",
    ]


@pytest.mark.target(TARGET_WITH_BASE_TARGET)
def test_exclude_base_target(target, catalog):
    # When `BaseTarget` is in the target's module namespace
    # Then it should not be listed in available variants
    assert list(loader.get_all_variants(catalog=catalog)) == ["my_target"]


@pytest.mark.target(TARGET_WITH_EXCLUDED_BASE_CLASS)
def test_exclude_by_attribute(target, catalog):
    # When there is a class that is explicitly excluded from collection
    # Then it should not be listed in available variants
    assert list(loader.get_all_variants(catalog=catalog)) == ["my_target"]
