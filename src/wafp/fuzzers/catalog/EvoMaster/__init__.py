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
        return [
            "--blackBox=true",
            f"--bbSwaggerUrl={schema}",
            "--outputFormat=JAVA_JUNIT_4",
            "--maxTime=30s",
            "--ratePerMinute=60",
        ]
