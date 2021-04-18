import pathlib
from typing import Dict, List

import requests

from wafp.fuzzers import BaseFuzzer, FuzzerContext
from wafp.utils import is_url


class Default(BaseFuzzer):
    def prepare_schema(self, context: FuzzerContext, schema: str) -> str:
        if not is_url(schema):
            # The default implementation will copy this file into container
            return super().prepare_schema(context, schema)
        # Cats works only with local files
        response = requests.get(schema)
        response.raise_for_status()
        filename = "schema.yaml"
        schema_file = context.input_directory / filename
        schema_file.write_bytes(response.content)
        container_input = self.get_container_input_directory()
        return str(container_input / filename)

    def get_container_output_directory(self) -> pathlib.Path:
        return pathlib.Path("/app/test-report/")

    def get_entrypoint_args(
        self, context: FuzzerContext, schema: str, base_url: str, headers: Dict[str, str]
    ) -> List[str]:
        args = [f"--contract={schema}", f"--server={base_url}"]
        if headers:
            # Over-simplified YAML serialization only for this exact case
            content = "\n".join(f"    {name}: {value}" for name, value in headers.items())
            filename = "headers.yaml"
            headers_file = context.input_directory / filename
            headers_file.write_text(f"all:\n{content}")
            container_input = self.get_container_input_directory()
            args.append(f"--headers={container_input / filename}")
        return args
