from wafp.targets import BaseTarget, Metadata, SchemaSource, SchemaSourceType, Specification, SpecificationType


class Default(BaseTarget):
    def get_base_url(self) -> str:
        return f"http://0.0.0.0:{self.port}/api"

    def get_schema_location(self) -> str:
        return f"http://0.0.0.0:{self.port}/api/swagger.json"

    def is_ready(self, line: bytes) -> bool:
        return b"Starting development server at" in line

    def get_metadata(self) -> Metadata:
        return Metadata.flask(
            flask_version="1.1.2",
            schema_source=SchemaSource(
                type=SchemaSourceType.STATIC,
                library=None,
            ),
            validation_from_schema=False,
            specification=Specification(name=SpecificationType.OPENAPI, version="2.0"),
        )


class Linked(Default):
    def get_schema_location(self) -> str:
        # API schema with the following links:
        #  POST /blog/posts -> DELETE /blog/posts/{postId}
        #  POST /blog/posts -> GET /blog/posts/{postId}
        #  POST /blog/posts -> PUT /blog/posts/{postId}
        #  DELETE /blog/posts/{postId} -> DELETE /blog/posts/{postId}
        #  DELETE /blog/posts/{postId} -> GET /blog/posts/{postId}
        #  DELETE /blog/posts/{postId} -> PUT /blog/posts/{postId}
        return str(self.path / "schema-with-links.json")
