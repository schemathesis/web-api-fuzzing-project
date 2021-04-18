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

FAST_API = Package(name="FastAPI", version="0.63.0")


class Default(BaseTarget):
    def get_base_url(self) -> str:
        return f"http://0.0.0.0:{self.port}/"

    def get_schema_location(self) -> str:
        return f"http://0.0.0.0:{self.port}/openapi.json"

    def is_ready(self, line: bytes) -> bool:
        return b"Uvicorn running on " in line

    def get_metadata(self) -> Metadata:
        return Metadata(
            language=Language.PYTHON,
            framework=FAST_API,
            schema_source=SchemaSource(type=SchemaSourceType.GENERATED, library=FAST_API),
            specification=Specification(name=SpecificationType.OPENAPI, version="3.0.2"),
            validation_from_schema=True,
        )


class WithOpenAPI3File(Default):
    """API schema is stored as a file."""

    def get_schema_location(self) -> str:
        return str(self.path / "openapi.json")

    def get_metadata(self) -> Metadata:
        return Metadata(
            language=Language.PYTHON,
            framework=FAST_API,
            schema_source=SchemaSource(type=SchemaSourceType.STATIC, library=FAST_API),
            specification=Specification(name=SpecificationType.OPENAPI, version="3.0.2"),
            validation_from_schema=True,
        )


class WithOpenAPI2File(Default):
    """API schema is converted to Open API 2.0 and stored as a file."""

    def get_schema_location(self) -> str:
        return str(self.path / "swagger.json")

    def get_metadata(self) -> Metadata:
        return Metadata(
            language=Language.PYTHON,
            framework=FAST_API,
            schema_source=SchemaSource(type=SchemaSourceType.STATIC, library=FAST_API),
            specification=Specification(name=SpecificationType.OPENAPI, version="2.0"),
            validation_from_schema=True,
        )
