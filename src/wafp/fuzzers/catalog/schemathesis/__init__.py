from typing import Dict, List, Optional

from wafp.fuzzers import BaseFuzzer


class Default(BaseFuzzer):
    def get_entrypoint_args(self, schema: str, base_url: str, headers: Optional[Dict[str, str]]) -> List[str]:
        args = [
            "run",
            schema,
            f"--base-url={base_url}",
            "--validate-schema=false",
            "--hypothesis-suppress-health-check=filter_too_much",
            "--debug-output-file=/tmp/wafp/output/out.jsonl",
        ]
        if headers is not None:
            for key, value in headers.items():
                args.extend(["-H", f"{key}: {value}"])
        return args


class AllChecks(Default):
    def get_entrypoint_args(self, schema: str, base_url: str, headers: Optional[Dict[str, str]]) -> List[str]:
        args = super().get_entrypoint_args(schema, base_url, headers)
        args.append("--checks=all")
        return args


class StatefulOld(Default):
    def get_entrypoint_args(self, schema: str, base_url: str, headers: Optional[Dict[str, str]]) -> List[str]:
        args = super().get_entrypoint_args(schema, base_url, headers)
        args.append("--stateful=links")
        return args
