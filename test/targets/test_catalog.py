import os
from subprocess import CalledProcessError

import pytest

from wafp.targets import loader
from wafp.targets.network import is_available


@pytest.fixture(params=loader.get_all_variants())
def target(request):
    cls = loader.by_name(request.param)
    target = cls()
    yield target
    target.stop()
    target.cleanup()


#
# def test_all_targets(target):
#     # Start & stop all implemented targets
#     try:
#         target.start()
#     except CalledProcessError as exc:
#         print(exc.stdout.decode("utf8", errors="replace"))
#         raise
#     target.get_metadata()
#     schema = target.get_schema_location()
#     if schema.startswith("/"):
#         assert os.path.exists(schema)
#     else:
#         assert is_available(schema)
#     artifacts = target.collect_artifacts()
#     assert len(artifacts) > 0
