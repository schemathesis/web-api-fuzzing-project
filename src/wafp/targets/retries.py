import random
from time import sleep
from typing import Tuple

from .errors import TargetNotAccessible
from .network import is_available

EXPONENTIAL_BASE = 2
JITTER = (0.0, 0.5)
INITIAL_RETRY_DELAY = 0.5
MAX_WAITING_RETRIES = 10


def wait(
    url: str,
    retries: int = MAX_WAITING_RETRIES,
    delay: float = INITIAL_RETRY_DELAY,
    jitter: Tuple[float, float] = JITTER,
) -> None:
    """Wait until `url` is available."""
    while retries > 0:
        if is_available(url):
            return
        retries -= 1
        delay *= EXPONENTIAL_BASE
        delay += random.uniform(*jitter)
        sleep(delay)
    raise TargetNotAccessible(f"{url} is not accessible")
