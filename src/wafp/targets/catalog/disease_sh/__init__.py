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
        return f"http://0.0.0.0:{self.port}/apidocs/swagger_v3.json"

    def is_ready(self, line: bytes) -> bool:
        return b"Your app is listening on port " in line

    def get_metadata(self) -> Metadata:
        return Metadata(
            language=Language.JAVASCRIPT,
            framework=Package(name="Express", version="4.17.1"),
            schema_source=SchemaSource(type=SchemaSourceType.STATIC, library=None),
            specification=Specification(name=SpecificationType.OPENAPI, version="2.0"),
            validation_from_schema=False,
        )
