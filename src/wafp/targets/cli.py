import argparse
import subprocess
from contextlib import suppress
from dataclasses import dataclass
from time import sleep
from typing import Optional

from . import loader
from .core import unused_port
from .docker_api import ensure_docker_version
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


def parse_args() -> CliArguments:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=list(loader.get_all_variants()))
    parser.add_argument("--port", required=False, type=int, default=unused_port())
    parser.add_argument("--no-cleanup", action="store_true", required=False, default=False)
    parser.add_argument("--build", action="store_true", required=False, default=False)
    parser.add_argument("--run-id", action="store", type=str, required=False)
    parser.add_argument("--sentry-dsn", action="store", type=str, required=False)
    parser.add_argument("--sentry-url", action="store", type=str, required=False)
    parser.add_argument("--sentry-token", action="store", type=str, required=False)
    parser.add_argument("--sentry-organization", action="store", type=str, required=False)
    parser.add_argument("--sentry-project", action="store", type=str, required=False)
    return CliArguments(**vars(parser.parse_args()))


def main() -> int:
    ensure_docker_version()
    args = parse_args()
    cls = loader.by_name(args.target)
    if cls is None:
        raise ValueError(f"Target `{args.target}` is not found")
    kwargs = {"port": args.port, "build": args.build, "sentry_dsn": args.sentry_dsn}
    if args.run_id is not None:
        kwargs["run_id"] = args.run_id  # type: ignore
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
        if not args.no_cleanup:
            target.cleanup()


if __name__ == "__main__":
    main()
