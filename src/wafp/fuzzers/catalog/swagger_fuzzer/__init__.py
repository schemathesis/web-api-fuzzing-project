from typing import Dict, List

from wafp.fuzzers import BaseFuzzer, FuzzerContext
from wafp.utils import is_url


class Default(BaseFuzzer):
    def prepare_schema(self, context: FuzzerContext, schema: str) -> str:
        if is_url(schema):
            return schema
        # Swagger-fuzzer doesn't support loading API schemas from files at all
        return self.serve_spec(context, schema)

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

        # Swagger-fuzzer does not support setting base URL or custom headers
        return [schema]
