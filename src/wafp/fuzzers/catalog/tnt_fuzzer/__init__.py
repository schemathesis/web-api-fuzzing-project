import json
from typing import Dict, List
from urllib.parse import urlparse

from wafp.fuzzers import BaseFuzzer, FuzzerContext
from wafp.utils import is_url


class Default(BaseFuzzer):
    def prepare_schema(self, context: FuzzerContext, schema: str) -> str:
        if is_url(schema):
            return schema
        # TnT-Fuzzer doesn't support loading API schemas from files at all
        return self.serve_spec(context, schema)

    def get_entrypoint_args(
        self, context: FuzzerContext, schema: str, base_url: str, headers: Dict[str, str]
    ) -> List[str]:
        parsed = urlparse(base_url)
        args = [
            f"--url={schema}",
            f"--basepath={parsed.path}",
            f"--host={parsed.netloc}",
            "--log_all",
        ]
        if headers:
            serialized_headers = json.dumps(headers)
            args.append(f"--headers={serialized_headers}")
        return args
