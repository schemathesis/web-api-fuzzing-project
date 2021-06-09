from wafp.targets import (
    BaseTarget,
    Language,
    Metadata,
    SchemaSource,
    SchemaSourceType,
    Specification,
    SpecificationType,
)


class Default(BaseTarget):
    def get_base_url(self) -> str:
        return f"http://0.0.0.0:{self.port}/"

    def get_schema_location(self) -> str:
        return str(self.path / "schema.json")

    def is_ready(self, line: bytes) -> bool:
        return b"Serving under " in line

    def get_metadata(self) -> Metadata:
        return Metadata(
            language=Language.GO,
            framework=None,
            schema_source=SchemaSource(type=SchemaSourceType.STATIC, library=None),
            specification=Specification(name=SpecificationType.OPENAPI, version="2.0"),
            validation_from_schema=False,
        )
