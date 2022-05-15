from typing import Dict, List, Optional

from wafp.fuzzers import BaseFuzzer, FuzzerContext


class Default(BaseFuzzer):
    def get_entrypoint_args(
        self,
        context: FuzzerContext,
        schema: str,
        base_url: str,
        headers: Optional[Dict[str, str]],
        ssl_insecure: bool = False,
    ) -> List[str]:
        args = [schema]
        if headers is not None:
            for key, value in headers.items():
                args.extend(["-H", f"{key}: {value}"])
        return args
