from wafp.targets import BaseTarget, Metadata, Package, SchemaSource, SchemaSourceType, Specification, SpecificationType


class Default(BaseTarget):
    def get_base_url(self) -> str:
        return f"http://0.0.0.0:{self.port}/v1"

    def get_schema_location(self) -> str:
        return f"http://0.0.0.0:{self.port}/swagger/"

    def is_ready(self, line: bytes) -> bool:
        return b"Listening at: " in line

    def get_metadata(self) -> Metadata:
        return Metadata.flask(
            flask_version="1.1.1",
            schema_source=SchemaSource(
                type=SchemaSourceType.MIXED,
                library=Package(
                    name="flask-apispec",
                    version="0.7.0",
                ),
            ),
            validation_from_schema=False,
            specification=Specification(name=SpecificationType.OPENAPI, version="2.0"),
        )
