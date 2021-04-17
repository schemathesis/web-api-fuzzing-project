import abc
import pathlib
import subprocess
import tempfile
import time
from shutil import copy2
from typing import Any, Dict, List, Optional, Tuple, Type, Union

import attr

from ..artifacts import Artifact, ArtifactType
from ..base import Component
from ..constants import DEFAULT_FUZZER_SERVICE_NAME, TEMPORARY_DIRECTORY_PREFIX
from ..utils import NOT_SET, NotSet, is_url


@attr.s()
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
        output_directory = tempdir / "output"
        output_directory.mkdir()
        return input_directory, output_directory

    def get_volumes_mountpoint_root(self) -> pathlib.Path:
        """In-container path to the attached volumes root."""
        return pathlib.Path("/tmp/wafp")

    def get_volumes(self, input_directory: pathlib.Path, output_directory: pathlib.Path) -> List[str]:
        """Docker volumes attached to fuzzer's container."""
        mountpoint = self.get_volumes_mountpoint_root()
        return [
            # Everything that is consumed by the container
            f"{input_directory}:{mountpoint / 'input'}",
            # All output of the container
            f"{output_directory}:{mountpoint / 'output'}",
        ]

    def prepare_schema(self, schema: str, input_directory: pathlib.Path) -> str:
        """Make API schema accessible by the fuzzer's container."""
        if is_url(schema):
            # Containers should work in the `host` network mode; therefore localhost's URLs should be accessible
            return schema
        # If `schema` is a filepath, then copy it to location accessible by the container
        copy2(schema, input_directory)
        # `input` directory on the host is mapped to `input` directory inside a container
        container_dir = self.get_volumes_mountpoint_root()
        return f"{container_dir / 'input'}/{pathlib.Path(schema).name}"

    def run(self, schema: str, base_url: str, headers: Optional[Dict[str, str]] = None) -> "FuzzResult":
        """Run fuzzer against an API schema."""
        input_directory, output_directory = self.get_input_output_directories()
        schema_location = self.prepare_schema(schema, input_directory)
        info: Dict[str, Any] = {"schema_location": schema_location, "base_url": base_url}
        if headers:
            info["headers"] = headers
        self.logger.info("Start fuzzer", **info)
        start = time.perf_counter()
        completed_process = self.compose.run(
            service=self.get_fuzzer_service_name(),
            args=self.get_entrypoint_args(schema_location, base_url, headers),
            entrypoint=self.get_entrypoint(),
            volumes=self.get_volumes(input_directory, output_directory),
        )
        self.logger.info(
            "Finish fuzzer", returncode=completed_process.returncode, duration=round(time.perf_counter() - start, 2)
        )
        return FuzzResult(
            fuzzer=self,
            completed_process=completed_process,
            output_directory=output_directory,
        )

    @abc.abstractmethod
    def get_entrypoint_args(self, schema: str, base_url: str, headers: Optional[Dict[str, str]]) -> List[str]:
        """Arguments to fuzzer's entrypoint in `docker-compose run <service> <args>`."""
        raise NotImplementedError

    def collect_artifacts(self, temp_dir: pathlib.Path) -> List[Artifact]:
        """Extract fuzzer's artifacts - additional logs, test cases, etc."""
        return [Artifact.log_file(str(path)) for path in temp_dir.iterdir()]


@attr.s()
class FuzzResult:
    """Results of a single fuzz run."""

    # Fuzzer itself
    fuzzer: BaseFuzzer = attr.ib()
    # Finished `docker-compose run` call
    completed_process: subprocess.CompletedProcess = attr.ib()
    # Temporary directory that is expected to have all container's output - logs, failing test cases, etc
    output_directory: pathlib.Path = attr.ib()

    def collect_artifacts(self) -> List[Artifact]:
        """Extract fuzz run's artifacts."""
        # Get stdout & delegate the rest to the fuzzer.
        artifacts = [
            Artifact.stdout(self.completed_process.stdout),
            *self.fuzzer.collect_artifacts(self.output_directory),
        ]
        self.fuzzer.logger.info(
            "Collect artifacts",
            logs=len([a for a in artifacts if a.type == ArtifactType.STDOUT]),
            log_files=len([a for a in artifacts if a.type == ArtifactType.LOG_FILE]),
        )
        return artifacts


Fuzzer = Type[BaseFuzzer]
