import json
from typing import Dict, List
from urllib.parse import urlparse

from wafp.fuzzers import BaseFuzzer, FuzzerContext
from wafp.utils import is_url


class Default(BaseFuzzer):
    def get_entrypoint_args(
        self, context: FuzzerContext, schema: str, base_url: str, headers: Dict[str, str]
    ) -> List[str]:
        if is_url(schema):
            args = [f"--src_url={schema}"]
        else:
            args = [f"-s={schema}"]
        parsed = urlparse(base_url)
        args.extend(
            [
                "-r=/tmp/wafp/output/",
                f"--url={parsed.scheme}://{parsed.netloc}/",
            ]
        )
        if headers:
            serialized_headers = json.dumps([headers])
            args.append(f"--headers={serialized_headers}")
        return args