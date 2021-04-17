import json
from typing import Dict, List, Optional
from urllib.parse import urlparse

from wafp.fuzzers import BaseFuzzer
from wafp.utils import is_url


class Default(BaseFuzzer):
    def get_entrypoint_args(self, schema: str, base_url: str, headers: Optional[Dict[str, str]]) -> List[str]:
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
        if headers is not None:
            serialized_headers = json.dumps([headers])
            args.append(f"--headers={serialized_headers}")
        return args
