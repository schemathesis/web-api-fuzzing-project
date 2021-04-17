from wafp.fuzzers import cli
from wafp.fuzzers.cli import parse_headers


def test_parse_headers():
    assert parse_headers(["A: 42", "B: 43"]) == {"A": "42", "B": "43"}


def test_arg_parsing(fuzzers_catalog, fuzzer_package):
    args = cli.parse_args(
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
        ],
        catalog=fuzzers_catalog.__name__,
    )
    assert args.fuzzer == "example_fuzzer"
    assert args.headers == {"A": "42", "B": "43"}


def test_main(fuzzers_catalog, fuzzer_package, target):
    # Running example fuzzer against example target
    target.start()
    exit_code = cli.main(
        ["example_fuzzer", "--schema", target.get_schema_location(), "--base-url", target.get_base_url()],
        catalog=fuzzers_catalog.__name__,
    )
    assert exit_code == 0
