class AmbiguousItemNameError(ValueError):
    """Can't decide what item to load."""


class VersionError(RuntimeError):
    """Installed system dependency version is not supported."""


class InvalidHeader(ValueError):
    """Invalid string for header."""
