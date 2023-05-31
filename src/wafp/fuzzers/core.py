import abc
import pathlib
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from shutil import copy2, rmtree
from typing import Any, Dict, Generator, List, Optional, Tuple, Type, Union

import attr

from ..artifacts import Artifact, ArtifactType
from ..base import Component
from ..constants import DEFAULT_FUZZER_SERVICE_NAME, TEMPORARY_DIRECTORY_PREFIX
from ..targets.network import unused_port
from ..utils import NOT_SET, NotSet, is_url


class BaseFuzzer(abc.ABC, Component):
    def get_entrypoint(self) -> Union[str, NotSet]:
        """Default docker-compose service entrypoint."""
        return NOT_SET

    def get_fuzzer_service_name(self) -> str:
        """Docker-compose service name."""
        return DEFAULT_FUZZER_SERVICE_NAME

    def get_input_output_directories(self) -> Tuple[pathlib.Path, pathlib.Path]:
        """Create two temporary directories to communicate with the fuzzer's container."""
        prefix = f"{TEMPORARY_DIRECTORY_PREFIX}{self.name}-{self.__class__.__name__}-"
        tempdir = pathlib.Path(tempfile.mkdtemp(prefix=prefix))
        input_directory = tempdir / "input"
        input_directory.mkdir()
        input_directory.chmod(0o777)
        output_directory = tempdir / "output"
        output_directory.mkdir()
        output_directory.chmod(0o777)
        return input_directory, output_directory

    def get_fuzzer_context(self, target: Optional[str] = None) -> "FuzzerContext":
        input_directory, output_directory = self.get_input_output_directories()
        return FuzzerContext(input_directory=input_directory, output_directory=output_directory, target=target)

    def get_container_input_directory(self) -> pathlib.Path:
        return pathlib.Path("/tmp/wafp/input")

    def get_container_output_directory(self) -> pathlib.Path:
        return pathlib.Path("/tmp/wafp/output")

    def get_volumes(self, context: "FuzzerContext") -> List[str]:
        """Docker volumes attached to fuzzer's container."""
        container_input = self.get_container_input_directory()
        container_output = self.get_container_output_directory()
        return [
            # Everything that is consumed by the container
            f"{context.input_directory}:{container_input}:Z",
            # All output of the container
            f"{context.output_directory}:{container_output}:Z",
        ]

    def prepare_schema(self, context: "FuzzerContext", schema: str) -> str:
        """Make API schema accessible by the fuzzer's container."""
        if is_url(schema):
            # Containers should work in the `host` network mode; therefore localhost's URLs should be accessible
            return schema
        # If `schema` is a filepath, then copy it to location accessible by the container
        copy2(schema, context.input_directory)
        # `input` directory on the host is mapped to `input` directory inside a container
        container_dir = self.get_container_input_directory()
        return str(container_dir / pathlib.Path(schema).name)

    def start(
        self,
        schema: str,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        ssl_insecure: bool = False,
        build: bool = False,
        target: Optional[str] = None,
    ) -> "FuzzResult":
        """Run fuzzer against an API schema."""
        if build:
            self.build()
        context = self.get_fuzzer_context(target)
        schema_location = self.prepare_schema(context, schema)
        headers = headers or {}
        info: Dict[str, Any] = {"schema_location": schema_location, "base_url": base_url}
        if headers:
            info["headers"] = headers
        self.logger.info("Start fuzzer", **info)
        start = time.perf_counter()
        completed_process = self.compose.run(
            service=self.get_fuzzer_service_name(),
            args=self.get_entrypoint_args(context, schema_location, base_url, headers, ssl_insecure),
            entrypoint=self.get_entrypoint(),
            volumes=self.get_volumes(context),
        )
        duration = round(time.perf_counter() - start, 2)
        self.logger.info("Finish fuzzer", returncode=completed_process.returncode, duration=duration)
        return FuzzResult(fuzzer=self, completed_process=completed_process, context=context, duration=duration)

    @contextmanager
    def run(
        self,
        schema: str,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        ssl_insecure: bool = False,
        build: bool = False,
        target: Optional[str] = None,
    ) -> Generator["FuzzResult", None, None]:
        """Run fuzzer as a context manager.

        It is a common workflow for CLI.
        """
        try:
            yield self.start(schema, base_url, headers, ssl_insecure, build, target)
        except subprocess.CalledProcessError as exc:
            sys.exit(exc.returncode)
        finally:
            self.stop()
            self.cleanup()

    def serve_spec(self, context: "FuzzerContext", schema: str) -> str:
        # The schema is served via a static file server
        copy2(schema, context.input_directory)
        port = unused_port()
        # The service should be stopped by calling `cleanup` after fuzzing is done
        self.compose.up(services=["static"], extra_env={"SERVE_INDEX": str(context.input_directory), "PORT": str(port)})
        filename = pathlib.Path(schema).name
        return f"http://0.0.0.0:{port}/{filename}"

    @abc.abstractmethod
    def get_entrypoint_args(
        self,
        context: "FuzzerContext",
        schema: str,
        base_url: str,
        headers: Dict[str, str],
        ssl_insecure: bool = False,
    ) -> List[str]:
        """Arguments to fuzzer's entrypoint in `docker-compose run <service> <args>`."""
        raise NotImplementedError

    def process_artifacts(self, result: "FuzzResult", output_dir: Union[str, pathlib.Path]) -> List[Artifact]:
        """Collect, clean and store all fuzzer's artifacts."""
        if isinstance(output_dir, str):
            output_dir = pathlib.Path(output_dir)
        raw_artifacts = result.collect_artifacts()
        output_dir.mkdir(exist_ok=True)
        for artifact in raw_artifacts:
            artifact.save_to(output_dir)
        return raw_artifacts

    def collect_artifacts(self, temp_dir: pathlib.Path) -> List[Artifact]:
        """Extract fuzzer's artifacts - additional logs, test cases, etc."""
        return [Artifact.log_file(str(path)) for path in temp_dir.iterdir()]


@attr.s()
class FuzzerContext:
    """Helpful context to prepare fuzzers."""

    input_directory: pathlib.Path = attr.ib()
    output_directory: pathlib.Path = attr.ib()
    target: Optional[str] = attr.ib(default=None)


@attr.s()
class FuzzResult:
    """Results of a single fuzz run."""

    # Fuzzer itself
    fuzzer: BaseFuzzer = attr.ib()
    # Finished `docker-compose run` call
    completed_process: subprocess.CompletedProcess = attr.ib()
    # Temporary directory that is expected to have all container's output - logs, failing test cases, etc
    context: FuzzerContext = attr.ib()
    # How long did the fuzzing process take in seconds
    duration: float = attr.ib()

    def collect_artifacts(self) -> List[Artifact]:
        """Extract fuzz run's artifacts."""
        # Get stdout & delegate the rest to the fuzzer.
        artifacts = [
            Artifact.stdout(self.completed_process.stdout),
            *self.fuzzer.collect_artifacts(self.context.output_directory),
        ]
        self.fuzzer.logger.info(
            "Collect artifacts",
            logs=len([a for a in artifacts if a.type == ArtifactType.STDOUT]),
            log_files=len([a for a in artifacts if a.type == ArtifactType.LOG_FILE]),
        )
        return artifacts

    def cleanup(self) -> None:
        """Clean temporary folders that are shared with the container."""
        try:
            rmtree(self.context.input_directory)
            rmtree(self.context.output_directory)
        except OSError:
            pass


Fuzzer = Type[BaseFuzzer]
