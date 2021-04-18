import argparse
import subprocess
import sys
from contextlib import suppress
from dataclasses import dataclass
from time import sleep
from typing import List, Optional

from ..docker import ensure_docker_version
from . import loader
from .core import unused_port
from .errors import TargetNotReady


@dataclass
class CliArguments:
    target: str
    port: int
    no_cleanup: bool
    build: bool
    run_id: Optional[str]
    sentry_dsn: Optional[str]
    sentry_url: Optional[str]
    sentry_token: Optional[str]
    sentry_organization: Optional[str]
    sentry_project: Optional[str]


def parse_args(args: List[str], *, catalog: Optional[str] = None) -> CliArguments:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=list(loader.get_all_variants(catalog=catalog)), help="Fuzz target to start")
    parser.add_argument(
        "--port", required=False, type=int, default=unused_port(), help="TCP port on localhost used for the fuzz target"
    )
    parser.add_argument(
        "--no-cleanup", action="store_true", required=False, default=False, help="Do not perform any cleanup on exit"
    )
    parser.add_argument(
        "--build", action="store_true", required=False, default=False, help="Force building docker images"
    )
    parser.add_argument(
        "--run-id",
        action="store",
        type=str,
        required=False,
        help="Explicit ID used to identify different runs in Sentry",
    )
    parser.add_argument("--sentry-dsn", action="store", type=str, required=False, help="Sentry DSN for the fuzz target")
    parser.add_argument("--sentry-url", action="store", type=str, required=False, help="Sentry instance base URL")
    parser.add_argument("--sentry-token", action="store", type=str, required=False, help="Sentry access token")
    parser.add_argument(
        "--sentry-organization",
        action="store",
        type=str,
        required=False,
        help="The slug of the Sentry organization the fuzz target project belongs to",
    )
    parser.add_argument(
        "--sentry-project", action="store", type=str, required=False, help="The slug of the Sentry project"
    )
    return CliArguments(**vars(parser.parse_args(args)))


def main(args: Optional[List[str]] = None, *, catalog: Optional[str] = None) -> int:
    ensure_docker_version()
    args = args or sys.argv[1:]
    parsed_args = parse_args(args, catalog=catalog)
    cls = loader.by_name(parsed_args.target, catalog=catalog)
    if cls is None:
        raise ValueError(f"Target `{parsed_args.target}` is not found")
    kwargs = {"port": parsed_args.port, "force_build": parsed_args.build, "sentry_dsn": parsed_args.sentry_dsn}
    if parsed_args.run_id is not None:
        kwargs["run_id"] = parsed_args.run_id  # type: ignore
    target = cls(**kwargs)  # type: ignore
    try:
        target.start()
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    except TargetNotReady:
        target.cleanup()
    try:
        with suppress(KeyboardInterrupt):
            while True:
                sleep(1)
        return 0
    finally:
        target.stop()
        if not parsed_args.no_cleanup:
            target.cleanup()


if __name__ == "__main__":
    main()
