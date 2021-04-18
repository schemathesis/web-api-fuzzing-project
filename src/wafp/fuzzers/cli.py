import argparse
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional

from wafp.docker import ensure_docker_version

from . import loader
from .errors import InvalidHeader


@dataclass
class CliArguments:
    fuzzer: str
    schema: str
    base_url: str
    build: bool
    headers: Optional[Dict[str, str]]


def parse_headers(headers: List[str]) -> Dict[str, str]:
    """Convert headers to a dictionary.

    E.g. ["Foo: bar", "Spam: baz"] => {"Foo": "bar", "Spam": "baz"}
    """
    out = {}
    for header in headers or ():
        try:
            key, value = header.split(":", maxsplit=1)
        except ValueError:
            raise InvalidHeader(f"Headers should be in KEY:VALUE format. Got: {header}") from None
        value = value.lstrip()
        key = key.strip()
        out[key] = value
    return out


def parse_args(args: List[str], *, catalog: Optional[str] = None) -> CliArguments:
    parser = argparse.ArgumentParser()
    parser.add_argument("fuzzer", choices=list(loader.get_all_variants(catalog=catalog)), help="Fuzzer to run")
    parser.add_argument(
        "--schema",
        action="store",
        required=True,
        type=str,
    )
    parser.add_argument(
        "--base-url",
        action="store",
        required=True,
        type=str,
    )
    parser.add_argument(
        "--build", action="store_true", required=False, default=False, help="Force building docker images"
    )
    parser.add_argument(
        # Should be in form "NAME:VALUE"
        "--headers",
        "-H",
        type=str,
        action="extend",
        nargs="*",
    )
    kwargs = vars(parser.parse_args(args))
    if "headers" in kwargs:
        kwargs["headers"] = parse_headers(kwargs["headers"])
    return CliArguments(**kwargs)


def main(args: Optional[List[str]] = None, *, catalog: Optional[str] = None) -> int:
    """Run fuzzer against an API schema."""
    ensure_docker_version()
    args = args or sys.argv[1:]
    parsed_args = parse_args(args, catalog=catalog)
    cls = loader.by_name(parsed_args.fuzzer, catalog=catalog)
    if cls is None:
        raise ValueError(f"Fuzzer `{parsed_args.fuzzer}` is not found")
    fuzzer = cls()  # type: ignore
    if parsed_args.build:
        fuzzer.build()
    result = fuzzer.run(parsed_args.schema, parsed_args.base_url, parsed_args.headers)
    result.collect_artifacts()
    fuzzer.stop()
    fuzzer.cleanup()
    return result.completed_process.returncode


if __name__ == "__main__":
    main()
