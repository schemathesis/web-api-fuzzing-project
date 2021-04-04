from wafp.targets import BaseTarget, Metadata


class Default(BaseTarget):
    def get_base_url(self) -> str:
        return f"http://0.0.0.0:{self.port}/"

    def get_schema_location(self) -> str:
        return f"http://0.0.0.0:{self.port}/v1/spec"

    def is_ready(self, line: bytes) -> bool:
        return b"* Running on" in line

    def get_metadata(self) -> Metadata:
        return Metadata.flasgger(flask_version="1.1.2", flasgger_version="0.9.5", openapi_version="2.0")
