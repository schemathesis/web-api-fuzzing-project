import os

WAIT_TARGET_READY_TIMEOUT = 600
COMPOSE_PROJECT_NAME_PREFIX = "wafp_" + os.environ.get("PYTEST_XDIST_WORKER", "")
TEMPORARY_DIRECTORY_PREFIX = "wafp-"
MINIMUM_DOCKER_COMPOSE_VERSION = "1.28.0"
MINIMUM_DOCKER_VERSION = "20.10.0"
DEFAULT_DOCKER_COMPOSE_FILENAME = "docker-compose.yml"
DEFAULT_FUZZER_SERVICE_NAME = "fuzzer"
