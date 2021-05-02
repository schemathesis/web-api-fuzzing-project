import argparse
import sys
from dataclasses import dataclass
from typing import List, Optional

from . import fuzzers, targets
from .docker import ensure_docker_version


@dataclass
class CliArguments(targets.cli.SharedCliArguments, fuzzers.cli.SharedCliArguments):
    """Input arguments for CLI.

    They are composed from arguments to Fuzzers and Targets CLIs to avoid code duplication.
    """

    build: bool

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
        parser.add_argument(
            "--build", action="store_true", required=False, default=False, help="Force building docker images"
        )
        return cls.from_parser(args or sys.argv[1:], parser)

    @classmethod
    def extend_parser(cls, parser: argparse.ArgumentParser, *, catalog: Optional[str] = None) -> None:
        parser.add_argument(
            "--build", action="store_true", required=False, default=False, help="Force building docker images"
        )


def main(
    args: Optional[List[str]] = None, *, fuzzers_catalog: Optional[str] = None, targets_catalog: Optional[str] = None
) -> int:
    ensure_docker_version()
    cli_args = CliArguments.from_all_args(args, fuzzers_catalog=fuzzers_catalog, targets_catalog=targets_catalog)
    target = cli_args.get_target(catalog=targets_catalog)
    fuzzer = cli_args.get_fuzzer(catalog=fuzzers_catalog)
    with target.run(cli_args.no_cleanup) as context:
        result = fuzzer.run(
            schema=context.schema_location, base_url=context.base_url, headers=context.headers, build=cli_args.build
        )
        result.collect_artifacts()
        fuzzer.stop()
        fuzzer.cleanup()
    return result.completed_process.returncode


if __name__ == "__main__":
    main()
