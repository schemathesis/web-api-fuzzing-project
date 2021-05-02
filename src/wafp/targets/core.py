import abc
import subprocess
import sys
import time
from contextlib import contextmanager
from typing import Dict, Generator, List, Optional, Type

import attr

from ..artifacts import Artifact
from ..base import Component
from ..constants import WAIT_TARGET_READY_TIMEOUT
from . import sentry
from .errors import TargetNotReady
from .metadata import Metadata
from .network import unused_port
from .retries import wait


def generate_run_id() -> str:
    return str(int(time.time()))


@attr.s()
class BaseTarget(abc.ABC, Component):
    port: int = attr.ib(factory=unused_port)
    force_build: bool = attr.ib(default=False)
    sentry_dsn: Optional[str] = attr.ib(default=None)
    run_id: str = attr.ib(factory=generate_run_id)
    wait_target_ready_timeout: int = WAIT_TARGET_READY_TIMEOUT

    def start(self) -> "TargetContext":
        """Start the target.

        It will be ready to serve requests after this method is called.
        """
        self.logger.msg("Start target")
        start = time.perf_counter()
        deadline = time.time() + self.wait_target_ready_timeout
        self.compose.up(timeout=self.wait_target_ready_timeout, build=self.force_build)
        base_url = self.get_base_url()
        # Wait until base URL is accessible
        wait(base_url)
        headers = {}
        # Then extract important information from logs
        # And decide from logs whether the service is ready
        for line in self.compose.log_stream(deadline=deadline):
            headers.update(self.get_headers(line))
            if self.is_ready(line):
                break
        else:
            message = "Target is not ready in time"
            self.logger.error(message, timeout=self.wait_target_ready_timeout, logs=self.compose.logs())
            raise TargetNotReady(message)

        logs = self.compose.logs()
        self.after_start(logs.stdout, headers)
        info = {
            "duration": round(time.perf_counter() - start, 2),
            "address": base_url,
            "schema": self.get_schema_location(),
        }
        if headers:
            info["headers"] = headers
        self.logger.msg("Target is ready", **info)
        return TargetContext(base_url=base_url, schema_location=self.get_schema_location(), headers=headers)

    # These methods are expected to be overridden

    @abc.abstractmethod
    def get_base_url(self) -> str:
        """Target base URL."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_schema_location(self) -> str:
        """Full URL of API schema."""
        raise NotImplementedError

    @abc.abstractmethod
    def is_ready(self, line: bytes) -> bool:
        """Detect whether the target is ready."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_metadata(self) -> Metadata:
        """Target meta information."""
        raise NotImplementedError

    def get_environment_variables(self) -> Dict[str, str]:
        """Environment variables for docker-compose."""
        env = super().get_environment_variables()
        env.update({"PORT": str(self.port), "WAFP_RUN_ID": self.run_id})
        if self.sentry_dsn is not None:
            env["SENTRY_DSN"] = self.sentry_dsn
        return env

    def get_headers(self, line: bytes) -> Dict[str, str]:
        """Extract headers from docker-compose output lines."""
        return {}

    def after_start(self, stdout: bytes, headers: Dict[str, str]) -> None:
        """Additional actions after the target is ready.

        E.g. create a user, login, etc.
        """

    def collect_artifacts(
        self,
        sentry_url: Optional[str] = None,
        sentry_token: Optional[str] = None,
        sentry_organization: Optional[str] = None,
        sentry_project: Optional[str] = None,
    ) -> List[Artifact]:
        """Extract useful artifacts from fuzzing targets.

        By default it includes only target's stdout logs, but may also collect Sentry events for this run.

        It could also collect logs that are stored in containers directly.
        """
        artifacts = [Artifact.stdout(self.compose.logs().stdout)]
        if sentry_url and sentry_token and sentry_organization and sentry_project:
            events = sentry.list_events(sentry_url, sentry_token, sentry_organization, sentry_project, self.run_id)
            artifacts.extend(map(Artifact.sentry_event, events))
        return artifacts

    @contextmanager
    def run(self, no_cleanup: bool = False) -> Generator["TargetContext", None, None]:
        try:
            yield self.start()
        except subprocess.CalledProcessError as exc:
            sys.exit(exc.returncode)
        except TargetNotReady:
            sys.exit(1)
        finally:
            self.stop()
            if not no_cleanup:
                self.cleanup()


@attr.s(slots=True)
class TargetContext:
    base_url: str = attr.ib()
    schema_location: str = attr.ib()
    headers: Dict[str, str] = attr.ib()


Target = Type[BaseTarget]
