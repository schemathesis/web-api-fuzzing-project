import json
import pathlib
from shutil import copy2
from typing import Dict, List, Optional
from urllib.parse import urlparse

from wafp.fuzzers import BaseFuzzer
from wafp.targets.network import unused_port
from wafp.utils import is_url


class Default(BaseFuzzer):
    def prepare_schema(self, schema: str, input_directory: pathlib.Path) -> str:
        if is_url(schema):
            return schema
        # TnT-Fuzzer doesn't support loading API schemas from files at all
        # The schema is served via a static file server
        copy2(schema, input_directory)
        port = unused_port()
        # The service should be stopped by calling `cleanup` after fuzzing is done
        self.compose.up(services=["static"], extra_env={"SERVE_INDEX": str(input_directory), "PORT": str(port)})
        filename = pathlib.Path(schema).name
        return f"http://0.0.0.0:{port}/{filename}"

    def get_entrypoint_args(self, schema: str, base_url: str, headers: Optional[Dict[str, str]]) -> List[str]:
        parsed = urlparse(base_url)
        args = [
            f"--url={schema}",
            f"--basepath={parsed.path}",
            f"--host={parsed.netloc}",
            "--log_all",
        ]
        if headers is not None:
            serialized_headers = json.dumps(headers)
            args.append(f"--headers={serialized_headers}")
        return args
