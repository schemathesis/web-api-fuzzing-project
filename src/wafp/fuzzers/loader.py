from typing import Generator, List, Optional

from .. import loader
from . import catalog as default_catalog  # type: ignore
from .core import BaseFuzzer, Fuzzer


def by_name(name: str, catalog: Optional[str] = None) -> Optional[Fuzzer]:
    """Get a target variant by name."""
    return loader.by_name(name, base=BaseFuzzer, catalog=catalog, default_catalog=default_catalog)


def load_all_variants(name: str, *, catalog: Optional[str] = None) -> List[Fuzzer]:
    """Load all variants for a target."""
    # https://github.com/python/mypy/issues/5374
    return loader.load_all_variants(
        name, base=BaseFuzzer, catalog=catalog, default_catalog=default_catalog  # type: ignore
    )


def get_all_variants(*, catalog: Optional[str] = None) -> Generator[str, None, None]:
    """Iterate over all targets and all their variants."""
    if catalog is not None:
        catalog_package = __import__(catalog, fromlist=catalog.split(".")[-1:])
    else:
        catalog_package = default_catalog
    yield from loader.get_all_variants(base=BaseFuzzer, catalog=catalog_package)
