from textwrap import dedent
from typing import Dict, List, Union

from wafp.fuzzers import BaseFuzzer, FuzzerContext
from wafp.utils import NotSet


class Default(BaseFuzzer):
    def get_entrypoint_args(
        self, context: FuzzerContext, schema: str, base_url: str, headers: Dict[str, str], ssl_insecure: bool = False
    ) -> List[str]:
        args = [
            "run",
            schema,
            f"--base-url={base_url}",
            "--validate-schema=false",
            "--hypothesis-suppress-health-check=filter_too_much,too_slow",
            "--hypothesis-deadline=None",
            "--debug-output-file=/tmp/wafp/output/out.jsonl",
            "--no-color",
        ]
        if headers:
            for key, value in headers.items():
                args.extend(["-H", f"{key}: {value}"])
        if ssl_insecure:
            args.extend(["--request-tls-verify=false"])
        extend_entrypoint_args(context, args)
        return args


def extend_entrypoint_args(context: FuzzerContext, args: List[str]) -> None:
    """Add target-specific entrypoint arguments."""
    if context.target is not None and context.target.startswith("age_of_empires_2_api"):
        # Its schema combines `swagger` and `openapi` keywords
        # Schemathesis can force the schema version
        args.append("--force-schema-version=30")


class AllChecks(Default):
    def get_entrypoint_args(
        self, context: FuzzerContext, schema: str, base_url: str, headers: Dict[str, str], ssl_insecure: bool = False
    ) -> List[str]:
        args = super().get_entrypoint_args(context, schema, base_url, headers, ssl_insecure)
        args.append("--checks=all")
        return args


class Negative(Default):
    def get_entrypoint_args(
        self, context: FuzzerContext, schema: str, base_url: str, headers: Dict[str, str], ssl_insecure: bool = False
    ) -> List[str]:
        args = super().get_entrypoint_args(context, schema, base_url, headers, ssl_insecure)
        args.append("--data-generation-method=negative")
        return args


class StatefulOld(Default):
    def get_entrypoint_args(
        self, context: FuzzerContext, schema: str, base_url: str, headers: Dict[str, str], ssl_insecure: bool = False
    ) -> List[str]:
        args = super().get_entrypoint_args(context, schema, base_url, headers, ssl_insecure)
        args.append("--stateful=links")
        return args


class StatefulNew(BaseFuzzer):
    def get_entrypoint(self) -> Union[str, NotSet]:
        return "pytest"

    def get_entrypoint_args(
        self, context: FuzzerContext, schema: str, base_url: str, headers: Dict[str, str], ssl_insecure: bool = False
    ) -> List[str]:
        if ssl_insecure:
            self.logger.warning("Explicit cert verification skip is not supported for this target yet")

        filename = "test_stateful.py"
        if context.target is not None and context.target.startswith("age_of_empires_2_api"):
            extra = {"force_schema_version": "30"}
        else:
            extra = {}
        test_file = context.input_directory / filename
        test_file.write_text(
            dedent(
                f"""
import json
import os
from urllib.parse import urlparse

import schemathesis
from hypothesis import settings, HealthCheck
from schemathesis.checks import not_a_server_error

if urlparse("{schema}").scheme != "":
    loader = schemathesis.from_uri
else:
    loader = schemathesis.from_path

extra = {extra}

schema = loader(
    "{schema}",
    base_url="{base_url}",
    validate_schema=False,
    **extra
)

class APIWorkflow(schema.as_state_machine()):

    def get_call_kwargs(self, case):
        return {{"headers": {headers}}}

    def validate_response(self, response, case, additional_checks=()):
        case.validate_response(
            response, checks=(not_a_server_error,), additional_checks=additional_checks
        )

TestCase = APIWorkflow.TestCase
TestCase.settings = settings(max_examples=100, suppress_health_check=HealthCheck.all(), deadline=None)
"""
            )
        )
        return [str(self.get_container_input_directory() / filename)]
