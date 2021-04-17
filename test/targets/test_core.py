import subprocess
from time import sleep

import pytest


@pytest.fixture
def running_target(target):
    target.compose.up()


def assert_until(func, max_retries=3, delay=0.5):
    current = 0
    while True:
        try:
            assert func()
            return
        except AssertionError:
            if max_retries <= current:
                raise
        current += 1
        sleep(delay)


def test_compose_up(target):
    output = target.compose.up().stdout
    assert b"wafp_example_target_web_1 ... done" in output


def test_compose_up_build(target):
    output = target.compose.up(build=True).stdout
    assert b"Building web" in output
    assert b"wafp_example_target_web_1 ... done" in output


@pytest.mark.usefixtures("running_target")
def test_compose_logs(target):
    assert_until(lambda: b"Uvicorn running on" in target.compose.logs().stdout)


@pytest.mark.usefixtures("running_target")
def test_compose_log_stream(target):
    # Collect the current logs as a stream without waiting
    logs = list(target.compose.log_stream(deadline=0))
    assert len(logs) > 0


@pytest.mark.usefixtures("running_target")
def test_compose_stop(target):
    assert b"Stopping wafp_example_target_web_1 ... done" in target.compose.stop().stdout


@pytest.mark.usefixtures("running_target")
def test_compose_rm(target):
    assert b"Removing wafp_example_target_web_1 ... done" in target.compose.rm().stdout


def test_manually_removed_image(target):
    # Build the target first
    target.compose.up()
    target.compose.stop()
    # When the user manually removes a relevant image
    subprocess.check_output(["docker", "rmi", f"{target.project_name}_web", "-f"])
    target.compose.up()
    # Then it should be rebuilt without asking for the user's input
    # And the target should run
    assert_until(
        lambda: b"Uvicorn running on http://0.0.0.0:80 (Press CTRL+C to quit)\n" in target.compose.logs().stdout
    )
