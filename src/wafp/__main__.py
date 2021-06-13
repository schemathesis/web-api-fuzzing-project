import argparse
import json
import pathlib
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from . import fuzzers, targets
from .docker import ensure_docker_version


@dataclass
class CliArguments(targets.cli.SharedCliArguments, fuzzers.cli.SharedCliArguments):
    """Input arguments for CLI.

    They are composed from arguments to Fuzzers and Targets CLIs to avoid code duplication.
    """

    build: bool
    output_dir: str

    @classmethod
    def from_all_args(
        cls,
        args: Optional[List[str]] = None,
        *,
        fuzzers_catalog: Optional[str] = None,
        targets_catalog: Optional[str] = None,
    ) -> "CliArguments":
        args = args or sys.argv[1:]
        parser = argparse.ArgumentParser()
        fuzzers.cli.SharedCliArguments.extend_parser(parser, catalog=fuzzers_catalog)
        targets.cli.SharedCliArguments.extend_parser(parser, catalog=targets_catalog)
        cls.extend_parser(parser)
        return cls.from_parser(args or sys.argv[1:], parser)

    @classmethod
    def extend_parser(cls, parser: argparse.ArgumentParser, *, catalog: Optional[str] = None) -> None:
        parser.add_argument(
            "--build", action="store_true", required=False, default=False, help="Force building docker images"
        )
        parser.add_argument(
            "--output-dir",
            action="store",
            required=True,
            type=str,
        )

    def get_target_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_target_kwargs()
        kwargs["force_build"] = self.build
        return kwargs


def main(
    args: Optional[List[str]] = None, *, fuzzers_catalog: Optional[str] = None, targets_catalog: Optional[str] = None
) -> int:
    ensure_docker_version()
    cli_args = CliArguments.from_all_args(args, fuzzers_catalog=fuzzers_catalog, targets_catalog=targets_catalog)
    target = cli_args.get_target(catalog=targets_catalog)
    fuzzer = cli_args.get_fuzzer(catalog=fuzzers_catalog)
    output_dir = pathlib.Path(cli_args.output_dir)
    with target.run(cli_args.no_cleanup, extra_env={"WAFP_FUZZER_ID": cli_args.fuzzer}) as context:
        with fuzzer.run(
            schema=context.schema_location,
            base_url=context.base_url,
            headers=context.headers,
            build=cli_args.build,
            target=cli_args.target,
        ) as result:
            output_dir.mkdir(exist_ok=True)
            fuzzer.process_artifacts(result, output_dir / "fuzzer")
            target.process_artifacts(
                output_dir=output_dir / "target",
                sentry_url=cli_args.sentry_url,
                sentry_token=cli_args.sentry_token,
                sentry_project=cli_args.sentry_project,
                sentry_organization=cli_args.sentry_organization,
            )
    store_metadata(output_dir, cli_args.fuzzer, cli_args.target, target.run_id, result.duration)
    return result.completed_process.returncode


def store_metadata(output_dir: pathlib.Path, fuzzer: str, target: str, run_id: str, duration: float) -> None:
    data = {"fuzzer": fuzzer, "target": target, "run_id": run_id, "duration": duration}
    with (output_dir / "metadata.json").open("w") as fd:
        json.dump(data, fd)


if __name__ == "__main__":
    main()
