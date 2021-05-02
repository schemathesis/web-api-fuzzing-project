from typing import List, Optional

from ..docker import ensure_docker_version
from .cli import CliArguments


def main(args: Optional[List[str]] = None, *, catalog: Optional[str] = None) -> int:
    """Run a fuzzer against a target."""
    ensure_docker_version()
    cli_args = CliArguments.from_args(args, catalog=catalog)
    fuzzer = cli_args.get_fuzzer(catalog=catalog)
    result = fuzzer.run(
        schema=cli_args.schema, base_url=cli_args.base_url, headers=cli_args.headers, build=cli_args.build
    )
    result.collect_artifacts()
    fuzzer.stop()
    fuzzer.cleanup()
    return result.completed_process.returncode


if __name__ == "__main__":
    main()
