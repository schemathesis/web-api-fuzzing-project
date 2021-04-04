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
        return f"http://0.0.0.0:{self.port}/v1"

    def get_schema_location(self) -> str:
        return f"http://0.0.0.0:{self.port}/v1/?format=openapi"

    def is_ready(self, line: bytes) -> bool:
        return b"Starting development server at" in line

    def get_metadata(self) -> Metadata:
        return Metadata(
            language=Language.PYTHON,
            framework=Package(name="Django", version="2.2.13"),
            schema_source=SchemaSource(
                type=SchemaSourceType.GENERATED, library=Package(name="drf-yasg", version="1.17.1")
            ),
            specification=Specification(name=SpecificationType.OPENAPI, version="2.0"),
        )
