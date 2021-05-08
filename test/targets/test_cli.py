from wafp.targets import cli


def test_arg_parsing(targets_catalog, target_package, artifacts_dir):
    target = "example_target:Default"
    args = cli.CliArguments.from_args([target, "--output-dir", str(artifacts_dir)], catalog=targets_catalog.__name__)
    assert args.target == target
