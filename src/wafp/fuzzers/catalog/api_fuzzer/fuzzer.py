#!/usr/bin/env python3 -X utf8
# type: ignore
import argparse
import sys
import tempfile
from logging import _nameToLevel as levelNames

from apifuzzer.fuzz_utils import get_api_definition_from_file, get_api_definition_from_url
from apifuzzer.fuzzer_target.fuzz_request_sender import FuzzerTarget
from apifuzzer.openapi_template_generator import OpenAPITemplateGenerator
from apifuzzer.server_fuzzer import OpenApiServerFuzzer
from apifuzzer.utils import json_data, set_logger
from kitty.interfaces.base import EmptyInterface
from kitty.model import GraphModel


class Fuzzer:
    def __init__(
        self,
        api_resources,
        report_dir,
        test_level,
        log_level,
        basic_output,
        alternate_url=None,
        test_result_dst=None,
        auth_headers=None,
        api_definition_url=None,
        junit_report_path=None,
    ):
        self.api_resources = api_resources
        self.base_url = None
        self.alternate_url = alternate_url
        self.templates = None
        self.test_level = test_level
        self.report_dir = report_dir
        self.test_result_dst = test_result_dst
        self.auth_headers = auth_headers if auth_headers else {}
        self.junit_report_path = junit_report_path
        self.logger = set_logger(log_level, basic_output)
        self.logger.info("APIFuzzer initialized")
        self.api_definition_url = api_definition_url

    def prepare(self):
        # here we will be able to branch the template generator if we will support other than Swagger / OpenAPI
        template_generator = OpenAPITemplateGenerator(
            self.api_resources, logger=self.logger, api_definition_url=self.api_definition_url
        )
        template_generator.process_api_resources()
        self.templates = template_generator.templates
        self.base_url = template_generator.compile_base_url(self.alternate_url)

    def run(self):
        target = FuzzerTarget(
            name="target",
            base_url=self.base_url,
            report_dir=self.report_dir,
            auth_headers=self.auth_headers,
            junit_report_path=self.junit_report_path,
        )
        # WAFP: Replaced `WebInterface` with an empty one because it did not work well when tests are executed via
        # pytest-xdist
        interface = EmptyInterface()
        model = GraphModel()
        for template in self.templates:
            model.connect(template.compile_template())
        fuzzer = OpenApiServerFuzzer()
        fuzzer.set_model(model)
        fuzzer.set_target(target)
        fuzzer.set_interface(interface)
        fuzzer.start()
        try:
            fuzzer.stop()
        except AttributeError:
            pass


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1", "True", "T"):
        return True
    if v.lower() in ("no", "false", "f", "n", "0", "False", "F"):
        return False
    raise argparse.ArgumentTypeError("Boolean value expected.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="API fuzzer configuration",
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=20),
    )
    parser.add_argument(
        "-s",
        "--src_file",
        type=str,
        required=False,
        help="API definition file path. Currently only JSON format is supported",
        dest="src_file",
    )
    parser.add_argument(
        "--src_url",
        type=str,
        required=False,
        help="API definition url. Currently only JSON format is supported",
        dest="src_url",
    )
    parser.add_argument(
        "-r",
        "--report_dir",
        type=str,
        required=False,
        help="Directory where error reports will be saved. Default is temporally generated directory",
        dest="report_dir",
        default=tempfile.mkdtemp(),
    )
    parser.add_argument(
        "--level",
        type=int,
        required=False,
        help="Test deepness: [1,2], higher is the deeper !!!Not implemented!!!",
        dest="level",
        default=1,
    )
    parser.add_argument(
        "-u",
        "--url",
        type=str,
        required=False,
        help="Use CLI defined url instead compile the url from the API definition. Useful for testing",
        dest="alternate_url",
        default=None,
    )
    parser.add_argument(
        "-t",
        "--test_report",
        type=str,
        required=False,
        help="JUnit test result xml save path ",
        dest="test_result_dst",
        default=None,
    )
    parser.add_argument(
        "--log",
        type=str,
        required=False,
        help="Use different log level than the default WARNING",
        dest="log_level",
        default="warning",
        choices=[level.lower() for level in levelNames if isinstance(level, str)],
    )
    parser.add_argument(
        "--basic_output",
        type=str2bool,
        required=False,
        help="Use basic output for logging (useful if running in jenkins). Example --basic_output=True",
        dest="basic_output",
        default=False,
    )
    parser.add_argument(
        "--headers",
        type=json_data,
        required=False,
        help='Http request headers added to all request. Example: \'[{"Authorization": "SuperSecret"}, '
        '{"Auth2": "asd"}]\'',
        dest="headers",
        default=None,
    )
    args = parser.parse_args()
    api_definition_json = dict()
    if args.src_file:
        api_definition_json = get_api_definition_from_file(args.src_file)
    elif args.src_url:
        api_definition_json = get_api_definition_from_url(args.src_url)
    else:
        argparse.ArgumentTypeError("No API definition source provided -s, --src_file or --src_url should be defined")
        sys.exit(1)
    prog = Fuzzer(
        api_resources=api_definition_json,
        report_dir=args.report_dir,
        test_level=args.level,
        alternate_url=args.alternate_url,
        test_result_dst=args.test_result_dst,
        log_level=args.log_level,
        basic_output=args.basic_output,
        auth_headers=args.headers,
        api_definition_url=args.src_url,
        junit_report_path=args.test_result_dst,
    )
    prog.prepare()
    prog.run()
