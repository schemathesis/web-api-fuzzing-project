import pytest

from wafp.errors import InvalidHeader
from wafp.fuzzers import __main__, cli
from wafp.fuzzers.cli import parse_headers


def test_parse_headers():
    assert parse_headers(["A: 42", "B: 43"]) == {"A": "42", "B": "43"}


def test_parse_invalid_headers():
    with pytest.raises(InvalidHeader):
        parse_headers(["WRONG"])


def test_arg_parsing(fuzzers_catalog, fuzzer_package, artifacts_dir):
    args = cli.CliArguments.from_args(
        [
            "example_fuzzer",
            "--schema",
            "http://127.0.0.1/openapi.json",
            "--base-url",
            "http://127.0.0.1/",
            "-H",
            "A: 42",
            "-H",
            "B: 43",
            "--output-dir",
            str(artifacts_dir),
        ],
        catalog=fuzzers_catalog.__name__,
    )
    assert args.fuzzer == "example_fuzzer"
    assert args.headers == {"A": "42", "B": "43"}


def test_main(fuzzers_catalog, fuzzer_package, target, artifacts_dir):
    # Running example fuzzer against example target
    target.start()
    exit_code = __main__.main(
        [
            "example_fuzzer",
            "--schema",
            target.get_schema_location(),
            "--base-url",
            target.get_base_url(),
            "--output-dir",
            str(artifacts_dir),
        ],
        catalog=fuzzers_catalog.__name__,
    )
    assert exit_code == 0
    assert len(list(artifacts_dir.iterdir())) == 1
