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

    with target.run(cli_args.no_cleanup), suppress(KeyboardInterrupt):
        while True:
            sleep(1)
    return 0


if __name__ == "__main__":
    main()
