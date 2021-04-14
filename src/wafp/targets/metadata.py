import enum
from typing import Any, Optional

import attr


class Language(enum.Enum):
    PYTHON = enum.auto()
    GO = enum.auto()
    JAVASCRIPT = enum.auto()
    RUST = enum.auto()


class SpecificationType(enum.Enum):
    OPENAPI = enum.auto()


class SchemaSourceType(enum.Enum):
    # The whole API schema is manually written without help of automated tools
    STATIC = enum.auto()
    # The whole API schema is automatically generated via an automated tool
    GENERATED = enum.auto()
    # Some parts generated automatically, others are filled manually
    MIXED = enum.auto()


@attr.s()
class Specification:
    name: SpecificationType = attr.ib()
    version: str = attr.ib()


@attr.s()
class Package:
    name: str = attr.ib()
    version: str = attr.ib()


@attr.s()
class SchemaSource:
    type: SchemaSourceType = attr.ib()
    library: Optional[Package] = attr.ib()


@attr.s()
class Metadata:
    """Metadata about a target."""

    language: Language = attr.ib()
    framework: Optional[Package] = attr.ib()
    schema_source: SchemaSource = attr.ib()
    # Whether API schema is used to automatically validate input
    validation_from_schema: bool = attr.ib()
    specification: Specification = attr.ib()

    @classmethod
    def flasgger(
        cls, *, flask_version: str, flasgger_version: str, openapi_version: str, validation_from_schema: bool
    ) -> "Metadata":
        return cls.flask(
            flask_version=flask_version,
            schema_source=SchemaSource(
                # Flasgger processes Python docstrings and use them in the resulting schema
                type=SchemaSourceType.MIXED,
                library=Package(
                    name="flasgger",
                    version=flasgger_version,
                ),
            ),
            # Could be enabled with `Swagger(parse=True)` or `@swag_from('definitions.yml', validation=True)`
            validation_from_schema=validation_from_schema,
            specification=Specification(name=SpecificationType.OPENAPI, version=openapi_version),
        )

    @classmethod
    def flask(cls, *, flask_version: str, **kwargs: Any) -> "Metadata":
        return cls(language=Language.PYTHON, framework=Package(name="Flask", version=flask_version), **kwargs)
