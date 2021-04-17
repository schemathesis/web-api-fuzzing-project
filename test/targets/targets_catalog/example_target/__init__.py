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
        return f"http://0.0.0.0:{self.port}/openapi.json"

    def is_ready(self, line: bytes) -> bool:
        return b"Uvicorn running on " in line

    def get_metadata(self) -> Metadata:
        fastapi = Package(name="FastAPI", version="0.63.0")
        return Metadata(
            language=Language.PYTHON,
            framework=fastapi,
            schema_source=SchemaSource(type=SchemaSourceType.GENERATED, library=fastapi),
            specification=Specification(name=SpecificationType.OPENAPI, version="3.0"),
            validation_from_schema=True,
        )


class WithFile(Default):
    """API schema is stored as a file."""

    def get_schema_location(self) -> str:
        return str(self.path / "openapi.json")
