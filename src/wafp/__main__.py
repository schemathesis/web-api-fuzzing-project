import argparse
import sys
from dataclasses import dataclass
from typing import List, Optional

from . import fuzzers, targets
from .docker import ensure_docker_version


@dataclass
class CliArguments(targets.cli.SharedCliArguments, fuzzers.cli.SharedCliArguments):
    build: bool


def main(
    args: Optional[List[str]] = None, *, fuzzers_catalog: Optional[str] = None, targets_catalog: Optional[str] = None
) -> int:
    ensure_docker_version()
    parser = argparse.ArgumentParser()
    fuzzers.cli.SharedCliArguments.add_arguments(parser, catalog=fuzzers_catalog)
    targets.cli.SharedCliArguments.add_arguments(parser, catalog=targets_catalog)
    parser.add_argument(
        "--build", action="store_true", required=False, default=False, help="Force building docker images"
    )
    cli_args = CliArguments.parse_args(args or sys.argv[1:], parser)
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
