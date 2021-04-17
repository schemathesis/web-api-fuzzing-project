from typing import Dict, List, Optional

from wafp.fuzzers import BaseFuzzer


class Default(BaseFuzzer):
    def get_entrypoint_args(self, schema: str, base_url: str, headers: Optional[Dict[str, str]]) -> List[str]:
        args = [schema]
        if headers is not None:
            for key, value in headers.items():
                args.extend(["-H", f"{key}: {value}"])
        return args
