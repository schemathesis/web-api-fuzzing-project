import inspect
import re
from pkgutil import iter_modules
from types import ModuleType
from typing import Generator, List, Optional, Type

from . import catalog as default_catalog  # type: ignore
from .core import BaseTarget, Target
from .errors import AmbiguousTargetNameError


def by_name(target_name: str, catalog: Optional[str] = None) -> Optional[Target]:
    """Get a target variant by name."""
    package_name, variant_name = (re.split(r":(?![\\/])", target_name, 1) + [""])[:2]
    variants = load_all_variants(package_name, catalog=catalog)
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
    variant_names = ", ".join([f"{target_name}:{variant.__name__}" for variant in variants])
    raise AmbiguousTargetNameError(
        f"Target `{target_name}` defines multiple variants, and it is not clear which one to load. "
        f"You need to specify a fully qualified name. "
        f"Variants: {variant_names}"
    )


def load_all_variants(name: str, *, catalog: Optional[str] = None) -> List[Target]:
    """Load all variants for a target."""
    if catalog is not None:
        try:
            module = __import__(f"{catalog}.{name}", fromlist=[name])
        except ModuleNotFoundError:
            return []
    else:
        module = getattr(default_catalog, name, None)
        if module is None:
            return []
    return list(_iter_targets(module))


def get_all_variants(*, catalog: Optional[str] = None) -> Generator[str, None, None]:
    """Iterate over all targets and all their variants."""
    if catalog is not None:
        catalog_package = __import__(catalog)
    else:
        catalog_package = default_catalog
    for module_info in iter_modules(catalog_package.__path__):
        if module_info.ispkg:
            module = __import__(f"{catalog_package.__name__}.{module_info.name}", fromlist=[module_info.name])
            targets = [f"{module_info.name}:{cls.__name__}" for cls in _iter_targets(module)]
            if len(targets) == 1:
                # Yield only the base name if there is a single variant
                yield module_info.name
            else:
                yield from targets


def _iter_targets(module: ModuleType) -> Generator[Type[BaseTarget], None, None]:
    """Iterate over all subclasses of `BaseTarget` in the given module."""
    return (
        cls
        for _, cls in inspect.getmembers(module, inspect.isclass)
        if issubclass(cls, BaseTarget) and cls is not BaseTarget
    )
