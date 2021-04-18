from typing import Dict, List

from wafp.fuzzers import BaseFuzzer, FuzzerContext


class Default(BaseFuzzer):
    def get_entrypoint_args(
        self, context: FuzzerContext, schema: str, base_url: str, headers: Dict[str, str]
    ) -> List[str]:
        # Swagger-conformance does not support setting base URL or custom headers
        return [schema]
