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
        return str(self.path / "schema.yaml")

    def is_ready(self, line: bytes) -> bool:
        return b"Server listening on " in line

    def get_metadata(self) -> Metadata:
        return Metadata(
            language=Language.RUST,
            framework=Package(name="tide", version="0.14.0"),
            schema_source=SchemaSource(type=SchemaSourceType.STATIC, library=None),
            specification=Specification(name=SpecificationType.OPENAPI, version="3.0.3"),
        )
