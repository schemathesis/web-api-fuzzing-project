from wafp.targets import cli


def test_arg_parsing(targets_catalog, target_package):
    target = "example_target:Default"
    args = cli.CliArguments.parse([target], catalog=targets_catalog.__name__)
    assert args.target == target
