from typing import Dict, List

from wafp.fuzzers import BaseFuzzer, FuzzerContext


class Default(BaseFuzzer):
    def get_entrypoint_args(
        self, context: FuzzerContext, schema: str, base_url: str, headers: Dict[str, str]
    ) -> List[str]:
        # Fuzzy-Swagger does not support custom headers
        return [f"--swagger={schema}", f"--server={base_url}", "--verbose"]
