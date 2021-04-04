import os
from subprocess import CalledProcessError

import pytest

from wafp.targets import loader
from wafp.targets.network import is_available


@pytest.mark.parametrize("variant", loader.get_all_variants())
def test_all_targets(variant):
    cls = loader.by_name(variant)
    target = cls()
    try:
        target.start()
    except CalledProcessError as exc:
        print(exc.stdout.decode("utf8", errors="replace"))
        raise
    target.get_metadata()
    schema = target.get_schema_location()
    if schema.startswith("/"):
        assert os.path.exists(schema)
    else:
        assert is_available(schema)
    # cleanup should be more resilient. if test fails before this part, then some containers still could be running,
    # networks not removed, etc.
    target.stop()
    target.cleanup()
