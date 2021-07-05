from wafp.targets import BaseTarget, Metadata, SchemaSource, SchemaSourceType, Specification, SpecificationType


class Default(BaseTarget):
    def get_base_url(self) -> str:
        return f"http://0.0.0.0:{self.port}/api/v1"

    def get_schema_location(self) -> str:
        return f"http://0.0.0.0:{self.port}/apispec.json"

    def is_ready(self, line: bytes) -> bool:
        return b"uwsgi entered RUNNING state" in line

    def get_metadata(self) -> Metadata:
        return Metadata.flask(
            flask_version="1.1.2",
            schema_source=SchemaSource(
                # Even though `flasgger` is used to serve the API spec, it is static
                type=SchemaSourceType.STATIC,
                library=None,
            ),
            validation_from_schema=False,
            specification=Specification(name=SpecificationType.OPENAPI, version="3.0.0"),
        )


class Linked(Default):
    def get_schema_location(self) -> str:
        # API schema with the following links:
        #  - GET /civilizations => GET /civilization/{id}
        #  - GET /units => GET /unit/{id}
        #  - GET /structures => GET /structure/{id}
        #  - GET /technologies => GET /technology/{id}
        return str(self.path / "schema-with-links.json")
