from textwrap import dedent
from typing import Dict, List

from wafp.fuzzers import BaseFuzzer, FuzzerContext
from wafp.utils import is_url


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

        if not is_url(schema):
            # The `url` argument is ignored if we pass the `--schema` option
            args = [f"--schema={schema}", "http://0.0.0.0/any.yaml"]
        else:
            args = [schema]
        if headers:
            filename = "headers.py"
            headers_file = context.input_directory / filename
            headers_file.write_text(
                dedent(
                    f"""
            import fuzz_lightyear

            @fuzz_lightyear.victim_account
            def victim_factory():
                return {{
                    '_request_options': {{
                        'headers': {headers},
                    }}
                }}
            """
                )
            )
            container_input = self.get_container_input_directory()
            args.append(f"-f={container_input / filename}")
        return args
