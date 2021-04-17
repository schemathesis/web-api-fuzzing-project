import inspect
import re
from pkgutil import iter_modules
from types import ModuleType
from typing import Generator, List, Optional, TypeVar

from .errors import AmbiguousItemNameError

T = TypeVar("T", bound=type)
COLLECTION_ATTRIBUTE_NAME = "__collect__"


def by_name(name: str, *, base: T, catalog: Optional[str], default_catalog: ModuleType) -> Optional[T]:
    """Get a item variant by name."""
    package_name, variant_name = (re.split(r":(?![\\/])", name, 1) + [""])[:2]
    variants = load_all_variants(package_name, base=base, catalog=catalog, default_catalog=default_catalog)
    if variant_name:
        for variant in variants:
            if variant.__name__ == variant_name:
                return variant
        return None
    if len(variants) == 1:
        # Default variant
        return variants[0]
    if not variants:
        return None
    variant_names = ", ".join([f"{name}:{variant.__name__}" for variant in variants])
    raise AmbiguousItemNameError(
        f"`{name}` defines multiple variants, and it is not clear which one to load. "
        f"You need to specify a fully qualified name. "
        f"Variants: {variant_names}"
    )


def load_all_variants(name: str, *, base: T, catalog: Optional[str], default_catalog: ModuleType) -> List[T]:
    """Load all variants for an item."""
    if catalog is not None:
        try:
            module = __import__(f"{catalog}.{name}", fromlist=[name])
        except ModuleNotFoundError:
            return []
    else:
        module = getattr(default_catalog, name, None)
        if module is None:
            return []
    return list(iter_children(module, base=base))


def get_all_variants(*, base: T, catalog: ModuleType) -> Generator[str, None, None]:
    """Iterate over all items and all their variants."""
    # https://github.com/python/mypy/issues/1422
    for module_info in iter_modules(catalog.__path__):  # type: ignore
        if module_info.ispkg:
            module = __import__(f"{catalog.__name__}.{module_info.name}", fromlist=[module_info.name])
            items = [f"{module_info.name}:{cls.__name__}" for cls in iter_children(module, base=base)]
            if len(items) == 1:
                # Yield only the base name if there is a single variant
                yield module_info.name
            else:
                yield from items


def iter_children(module: ModuleType, base: T) -> Generator[T, None, None]:
    """Iterate over all subclasses of `base` in the given module."""
    return (
        cls
        for _, cls in inspect.getmembers(module, inspect.isclass)
        if issubclass(cls, base) and cls is not base and getattr(cls, COLLECTION_ATTRIBUTE_NAME, True)
    )
