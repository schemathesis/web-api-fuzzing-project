import argparse
import os
import pathlib
from typing import Generator, Optional, Tuple

import structlog
from dotenv import load_dotenv

from wafp.__main__ import main as run
from wafp.fuzzers import loader as fuzzers_loader
from wafp.targets import loader as targets_loader

logger = structlog.get_logger()
load_dotenv()

COMBINATIONS = {
    "age_of_empires_2_api:Default": {
        "fuzzers": [
            "api_fuzzer",
            "got_swag",
            "restler",
            "schemathesis:AllChecks",
            "schemathesis:Default",
            "schemathesis:Negative",
        ],
    },
    "age_of_empires_2_api:Linked": {
        "fuzzers": ["schemathesis:StatefulNew", "schemathesis:StatefulOld"],
    },
    "cccatalog_api:Default": {
        "fuzzers": ["got_swag", "restler", "schemathesis:AllChecks", "schemathesis:Default", "schemathesis:Negative"],
    },
    "cccatalog_api:Linked": {
        "fuzzers": ["schemathesis:StatefulNew"],
    },
    "covid19_japan_web_api:Default": {
        "fuzzers": [
            "api_fuzzer",
            "cats",
            "restler",
            "schemathesis:AllChecks",
            "schemathesis:Default",
            "schemathesis:Negative",
        ],
    },
    "covid19_japan_web_api:Linked": {
        "fuzzers": ["schemathesis:StatefulNew", "schemathesis:StatefulOld"],
    },
    "disease_sh:Default": {
        "fuzzers": ["api_fuzzer", "cats", "schemathesis:AllChecks", "schemathesis:Default", "schemathesis:Negative"]
    },
    "disease_sh:Linked": {"fuzzers": ["schemathesis:StatefulNew", "schemathesis:StatefulOld"]},
    "httpbin": {
        "fuzzers": ["api_fuzzer", "schemathesis:AllChecks", "schemathesis:Default", "schemathesis:Negative"],
    },
    "jupyter_server:Default": {
        "fuzzers": ["cats", "restler", "schemathesis:AllChecks", "schemathesis:Default", "schemathesis:Negative"],
    },
    "jupyter_server:Linked": {
        "fuzzers": ["schemathesis:StatefulNew", "schemathesis:StatefulOld"],
    },
    "jupyterhub:Default": {
        "fuzzers": ["schemathesis:AllChecks", "schemathesis:Default", "schemathesis:Negative"],
    },
    "jupyterhub:Linked": {
        "fuzzers": ["schemathesis:StatefulNew", "schemathesis:StatefulOld"],
    },
    "mailhog": {
        "fuzzers": [
            "api_fuzzer",
            "cats",
            "restler",
            "schemathesis:AllChecks",
            "schemathesis:Default",
            "schemathesis:Negative",
        ]
    },
    "open_fec:Default": {
        "fuzzers": [
            "api_fuzzer",
            "cats",
            "fuzz_lightyear",
            "got_swag",
            "restler",
            "schemathesis:AllChecks",
            "schemathesis:Default",
            "schemathesis:Negative",
            "swagger_fuzzer",
        ],
    },
    "open_fec:Linked": {
        "fuzzers": ["schemathesis:StatefulNew", "schemathesis:StatefulOld"],
    },
    "opentopodata": {
        "fuzzers": [
            "api_fuzzer",
            "cats",
            "restler",
            "schemathesis:AllChecks",
            "schemathesis:Default",
            "schemathesis:Negative",
        ],
    },
    "otto_parser": {"fuzzers": ["schemathesis:AllChecks", "schemathesis:Default", "schemathesis:Negative"]},
    "pslab_webapp": {
        "fuzzers": [
            "api_fuzzer",
            "cats",
            "fuzz_lightyear",
            "restler",
            "schemathesis:AllChecks",
            "schemathesis:Default",
            "schemathesis:Negative",
        ],
    },
    "pulpcore": {
        "fuzzers": [
            "api_fuzzer",
            "cats",
            "got_swag",
            "schemathesis:AllChecks",
            "schemathesis:Default",
            "schemathesis:Negative",
            "tnt_fuzzer",
        ],
    },
    "request_baskets:Default": {
        "fuzzers": [
            "api_fuzzer",
            "cats",
            "restler",
            "schemathesis:AllChecks",
            "schemathesis:Default",
            "schemathesis:Negative",
        ]
    },
    "request_baskets:Linked": {"fuzzers": ["schemathesis:StatefulNew", "schemathesis:StatefulOld"]},
    "restler_demo:Default": {
        "fuzzers": ["got_swag", "restler", "schemathesis:AllChecks", "schemathesis:Default", "schemathesis:Negative"],
    },
    "restler_demo:Linked": {
        "fuzzers": ["schemathesis:StatefulNew", "schemathesis:StatefulOld"],
    },
    "worklog:Default": {
        "fuzzers": ["api_fuzzer", "restler", "schemathesis:AllChecks", "schemathesis:Default", "schemathesis:Negative"],
    },
    "worklog:Linked": {
        "fuzzers": ["schemathesis:StatefulNew", "schemathesis:StatefulOld"],
    },
    "gitlab": {"fuzzers": ["schemathesis:Default"]},
}


def split_name(name: str) -> Tuple[str, Optional[str]]:
    return tuple(name.split(":", 1) + [None])[:2]  # type:ignore


def get_env_var_prefix(target: str) -> str:
    name, _ = split_name(target)
    return name.upper()


def get_sentry_dsn_env_var_name(target: str) -> str:
    prefix = get_env_var_prefix(target)
    return f"{prefix}_SENTRY_DSN"


def get_sentry_dsn(target: str) -> Optional[str]:
    env_var_name = get_sentry_dsn_env_var_name(target)
    return os.getenv(env_var_name)


def is_match(value: str, expected: str) -> bool:
    name, variant = split_name(value)
    expected_name, expected_variant = split_name(expected)
    return name == expected_name and (expected_variant is None or expected_variant == variant)


def expand_options(options: Generator[str, None, None]) -> list[str]:
    output = []
    for option in options:
        output.append(option)
        name, variant = split_name(option)
        if variant is not None:
            output.append(name)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        action="store",
        required=True,
        type=str,
    )
    parser.add_argument(
        "--iterations",
        action="store",
        default=30,
        type=int,
    )
    parser.add_argument("--fuzzer", choices=expand_options(fuzzers_loader.get_all_variants()), help="Fuzzer to run")
    parser.add_argument("--target", choices=expand_options(targets_loader.get_all_variants()), help="Target to run")
    return parser.parse_args()


def run_single(fuzzer: str, target: str, iteration: int, output_dir: pathlib.Path, sentry_dsn: Optional[str]) -> None:
    final_dir = output_dir / f"{fuzzer}-{target}-{iteration}"
    if final_dir.exists():
        print("The output directory exists! Skipping", final_dir)
        return
    args = [fuzzer, target, "--build", f"--output-dir={final_dir}"]
    if sentry_dsn is not None:
        args.append(f"--sentry-dsn={sentry_dsn}")
    run(args)


def main() -> None:
    args = parse_args()
    assert args.iterations >= 0, "The number of iterations should be a positive integer"
    output_dir = pathlib.Path(args.output_dir).absolute()
    for target, data in COMBINATIONS.items():
        if args.target and not is_match(target, args.target):
            continue
        sentry_dsn = get_sentry_dsn(target)
        for fuzzer in data.get("fuzzers", ()):
            if args.fuzzer and not is_match(fuzzer, args.fuzzer):
                continue
            if sentry_dsn:
                logger.info("Sentry is installed")
            else:
                logger.warn("Sentry is not installed")
            for iteration in range(1, args.iterations + 1):
                run_single(fuzzer, target, iteration, output_dir, sentry_dsn)


if __name__ == "__main__":
    main()
