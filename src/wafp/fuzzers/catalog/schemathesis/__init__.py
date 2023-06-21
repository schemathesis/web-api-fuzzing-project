import abc
import os
from textwrap import dedent
from typing import Dict, List, Optional, Union

from wafp.fuzzers import BaseFuzzer, FuzzerContext
from wafp.utils import NotSet

DEFAULT_MAX_EXAMPLES = 100


class BaseSchemathesisFuzzer(BaseFuzzer, abc.ABC):
    __collect__ = False

    @property
    def max_examples(self) -> int:
        return self.kwargs.get("max_examples", DEFAULT_MAX_EXAMPLES)


class Default(BaseSchemathesisFuzzer):
    @property
    def send_report_requested(self) -> bool:
        return bool(os.environ.get("SCHEMATHESIS_REPORT", False))

    @property
    def saas_token(self) -> Optional[str]:
        return os.environ.get("SCHEMATHESIS_TOKEN")

    @property
    def api_name(self) -> Optional[str]:
        return os.environ.get("SCHEMATHESIS_API_NAME")

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
            f"--hypothesis-max-examples={self.max_examples}",
            "--debug-output-file=/tmp/wafp/output/out.jsonl",
            "--no-color",
        ]
        if headers:
            for key, value in headers.items():
                args.extend(["-H", f"{key}: {value}"])
        if ssl_insecure:
            args.append("--request-tls-verify=false")
        if self.send_report_requested:
            self.logger.info("Report gonna be sent to schemathesis.io")
            args.append("--report")
        if self.saas_token:
            args.append(f"--schemathesis-io-token={self.saas_token}")
        extend_entrypoint_args(context, args)
        return args

    def get_environment_variables(self) -> Dict[str, str]:
        env = super().get_environment_variables()
        if self.api_name is not None:
            # This is a bit more convenient, as `API_NAME` is an optional positional argument to Schemathesis
            env["SCHEMATHESIS_API_NAME"] = self.api_name
        env["EXTRA_REQUIREMENTS"] = "empty-requirements.txt"
        return env


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


class NoMutations(Default):
    def get_environment_variables(self) -> Dict[str, str]:
        env = super().get_environment_variables()
        env["EXTRA_REQUIREMENTS"] = "ablation-mutation-requirements.txt"
        return env


class Negative(Default):
    def get_entrypoint_args(
        self, context: FuzzerContext, schema: str, base_url: str, headers: Dict[str, str], ssl_insecure: bool = False
    ) -> List[str]:
        args = super().get_entrypoint_args(context, schema, base_url, headers, ssl_insecure)
        args.append("--data-generation-method=negative")
        return args


class NegativeNoSwarm(Negative):
    def get_environment_variables(self) -> Dict[str, str]:
        env = super().get_environment_variables()
        env["SCHEMATHESIS_DISABLE_SWARM_TESTING"] = "true"
        return env


class NoFormats(Default):
    def get_environment_variables(self) -> Dict[str, str]:
        env = super().get_environment_variables()
        env["SCHEMATHESIS_DISABLE_FORMAT_STRATEGIES"] = "true"
        return env


class LessPreProcessing(Default):
    def get_environment_variables(self) -> Dict[str, str]:
        env = super().get_environment_variables()
        env["SCHEMATHESIS_USE_LESS_SCHEMA_PRE_PROCESSING"] = "true"
        return env


class Fast(Default):
    @property
    def max_examples(self) -> int:
        return 10


class StatefulOld(Default):
    def get_entrypoint_args(
        self, context: FuzzerContext, schema: str, base_url: str, headers: Dict[str, str], ssl_insecure: bool = False
    ) -> List[str]:
        args = super().get_entrypoint_args(context, schema, base_url, headers, ssl_insecure)
        args.append("--stateful=links")
        return args


class StatefulNew(BaseSchemathesisFuzzer):
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
TestCase.settings = settings(max_examples={self.max_examples}, suppress_health_check=list(HealthCheck), deadline=None)
"""
            )
        )
        return [str(self.get_container_input_directory() / filename)]
