from wafp.targets import BaseTarget, Metadata, SchemaSource, SchemaSourceType, Specification, SpecificationType


class Default(BaseTarget):
    def get_base_url(self) -> str:
        return f"http://0.0.0.0:{self.port}/"

    def get_schema_location(self) -> str:
        return str(self.path / "schema.json")

    def is_ready(self, line: bytes) -> bool:
        return b"uwsgi entered RUNNING state" in line

    def get_metadata(self) -> Metadata:
        return Metadata.flask(
            flask_version="1.1.2",
            schema_source=SchemaSource(
                type=SchemaSourceType.STATIC,
                library=None,
            ),
            specification=Specification(name=SpecificationType.OPENAPI, version="3.0.2"),
        )
