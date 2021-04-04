import pytest

from wafp.targets.errors import TargetNotAccessible
from wafp.targets.retries import wait


def test_wait_not_available():
    url = "http://127.0.0.1:1"
    with pytest.raises(TargetNotAccessible, match=f"{url} is not accessible"):
        wait(url, retries=1, delay=0, jitter=(0, 0))
