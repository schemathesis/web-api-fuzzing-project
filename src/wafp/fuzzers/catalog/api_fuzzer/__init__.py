import json
from typing import Dict, List
from urllib.parse import urlparse

from wafp.fuzzers import BaseFuzzer, FuzzerContext
from wafp.utils import is_url


class Default(BaseFuzzer):
    def get_entrypoint_args(
        self,
        context: FuzzerContext,
        schema: str,
        base_url: str,
        headers: Dict[str, str],
        ssl_insecure: bool = False,
    ) -> List[str]:
        if ssl_insecure:
            self.logger.warning("Explicit cert verification skip is not supported for this fuzzer yet")

        args = ["--basic_output=True"]
        if is_url(schema):
            args.append(f"--src_url={schema}")
        else:
            args.append(f"-s={schema}")
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
