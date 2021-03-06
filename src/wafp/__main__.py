import argparse
import json
import pathlib
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from wafp import fuzzers, targets
from wafp.docker import ensure_docker_version


@dataclass
class CliArguments(targets.cli.SharedCliArguments, fuzzers.cli.SharedCliArguments):
    """Input arguments for CLI.

    They are composed from arguments to Fuzzers and Targets CLIs to avoid code duplication.
    """

    build: bool
    output_dir: str
    fuzzer_skip_ssl_verify: bool

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
            "--fuzzer-skip-ssl-verify",
            action="store_true",
            required=False,
            default=False,
            help="Tells fuzzer to skip certificates verification in case of https",
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
            ssl_insecure=cli_args.fuzzer_skip_ssl_verify or context.fuzzer_skip_ssl_verify,
            build=cli_args.build,
            target=cli_args.target,
        ) as result:
            output_dir.mkdir(exist_ok=True, parents=True)
            fuzzer.process_artifacts(result, output_dir / "fuzzer")
            target.process_artifacts(
                output_dir=output_dir / "target",
                sentry_url=cli_args.sentry_url,
                sentry_token=cli_args.sentry_token,
                sentry_project=cli_args.sentry_project,
                sentry_organization=cli_args.sentry_organization,
            )
            result.cleanup()
    store_metadata(output_dir, cli_args.fuzzer, cli_args.target, target.run_id, result.duration)
    # workaround for poetry issue, in order to make wafp more friendly to CI-systems
    # see https://github.com/python-poetry/poetry/issues/2369
    # TODO: rollback this when 1.2.0 will be released.
    sys.exit(result.completed_process.returncode)


def store_metadata(output_dir: pathlib.Path, fuzzer: str, target: str, run_id: str, duration: float) -> None:
    data = {"fuzzer": fuzzer, "target": target, "run_id": run_id, "duration": duration}
    with (output_dir / "metadata.json").open("w") as fd:
        json.dump(data, fd)


if __name__ == "__main__":
    main()
