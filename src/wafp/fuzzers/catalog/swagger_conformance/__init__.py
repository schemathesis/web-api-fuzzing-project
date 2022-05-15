from typing import Dict, List

from wafp.fuzzers import BaseFuzzer, FuzzerContext


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

        # Swagger-conformance does not support setting base URL or custom headers
        return [schema]
