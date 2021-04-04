class AmbiguousTargetNameError(ValueError):
    """Can't decide what target to load."""


class TargetNotAccessible(RuntimeError):
    """Target is not accessible."""


class TargetNotReady(RuntimeError):
    """Target is not ready in time."""


class VersionError(RuntimeError):
    """Installed system dependency version is not supported."""
