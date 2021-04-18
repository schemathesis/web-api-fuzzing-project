from textwrap import dedent
from typing import Dict, List
from urllib.parse import urlparse

import requests

from wafp.fuzzers import BaseFuzzer, FuzzerContext
from wafp.utils import is_url


class Default(BaseFuzzer):
    def prepare_schema(self, context: FuzzerContext, schema: str) -> str:
        if not is_url(schema):
            # The default implementation will copy this file into container
            return super().prepare_schema(context, schema)
        # Restler works only with local files
        response = requests.get(schema)
        response.raise_for_status()
        if schema.endswith(".yaml"):
            filename = "schema.yaml"
        else:
            filename = "schema.json"
        schema_file = context.input_directory / filename
        schema_file.write_bytes(response.content)
        container_input = self.get_container_input_directory()
        return str(container_input / filename)

    def get_entrypoint_args(
        self, context: FuzzerContext, schema: str, base_url: str, headers: Dict[str, str]
    ) -> List[str]:
        parsed = urlparse(base_url)
        args = [
            str(self.get_container_output_directory()),
            schema,
            str(parsed.hostname),
            str(parsed.port),
        ]
        if headers:
            filename = "get_token.py"
            headers_file = context.input_directory / filename
            lines = "\n".join(f'print("{name}: {value}")' for name, value in headers.items())
            headers_file.write_text(
                dedent(
                    f"""
                print("{{}}")
                {lines}
                """
                )
            )
            container_input = self.get_container_input_directory()
            args.append(f"python {container_input / filename}")
        return args
