from contextlib import suppress
from time import sleep
from typing import List, Optional

from ..docker import ensure_docker_version
from .cli import CliArguments


def main(args: Optional[List[str]] = None, *, catalog: Optional[str] = None) -> int:
    """Spin up a target and run it until manually stopped."""
    ensure_docker_version()
    cli_args = CliArguments.from_args(args, catalog=catalog)
    target = cli_args.get_target(catalog=catalog)

    with target.run(cli_args.no_cleanup):
        with suppress(KeyboardInterrupt):
            while True:
                sleep(1)
        target.process_artifacts(
            output_dir=cli_args.output_dir,
            sentry_url=cli_args.sentry_url,
            sentry_token=cli_args.sentry_token,
            sentry_project=cli_args.sentry_project,
            sentry_organization=cli_args.sentry_organization,
        )

    return 0


if __name__ == "__main__":
    main()
