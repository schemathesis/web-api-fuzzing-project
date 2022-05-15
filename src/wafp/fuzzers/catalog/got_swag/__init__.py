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

        # Custom headers are only supported as variables for their tests DSL
        return [schema, "-m"]
