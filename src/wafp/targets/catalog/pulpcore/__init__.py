from typing import Dict

from wafp.targets import (
    BaseTarget,
    Language,
    Metadata,
    Package,
    SchemaSource,
    SchemaSourceType,
    Specification,
    SpecificationType,
)


class Default(BaseTarget):
    def get_base_url(self) -> str:
        return f"http://0.0.0.0:{self.port}/"

    def get_schema_location(self) -> str:
        return f"http://0.0.0.0:{self.port}/pulp/api/v3/docs/api.json"

    def is_ready(self, line: bytes) -> bool:
        return b"Watching for file changes with" in line

    def get_metadata(self) -> Metadata:
        return Metadata(
            language=Language.PYTHON,
            framework=Package(name="Django", version="2.2.17"),
            schema_source=SchemaSource(
                type=SchemaSourceType.GENERATED, library=Package(name="drf-spectacular", version="0.11.0")
            ),
            validation_from_schema=False,
            specification=Specification(name=SpecificationType.OPENAPI, version="3.0.3"),
        )

    def after_start(self, stdout: bytes, headers: Dict[str, str]) -> None:
        headers["Authorization"] = "Basic YWRtaW46dGVzdA=="
