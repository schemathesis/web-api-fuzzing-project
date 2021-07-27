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


class Linked(Default):
    def get_schema_location(self) -> str:
        # API schema with the following links:
        #  - GET /v3/covid-19/gov/ -> GET /v3/covid-19/gov/{country}
        #  - GET /v3/covid-19/apple/countries => GET /v3/covid-19/apple/countries/{country}
        #  - GET /v3/covid-19/apple/countries/{country} => GET /v3/covid-19/apple/countries/{country}/{subregions}
        #  - GET /v3/covid-19/nyt/counties -> GET /v3/covid-19/nyt/counties/{county}
        #  - GET /v3/covid-19/nyt/states -> GET /v3/covid-19/nyt/states/{state}
        #  - GET /v3/covid-19/historical/usacounties -> GET /v3/covid-19/historical/usacounties/{state}
        #  - GET /v3/covid-19/historical -> GET /v3/covid-19/historical/{country}
        #  - GET /v3/covid-19/historical/{country} -> GET /v3/covid-19/historical/{country}/{province}
        #  - GET /v3/covid-19/jhucsse/counties -> GET /v3/covid-19/jhucsse/counties/{county}
        #  - GET /v3/covid-19/countries -> GET /v3/covid-19/countries/{country}
        #  - GET /v3/covid-19/continents -> /v3/covid-19/continents/{continent}
        #  - GET /v3/covid-19/states -> /v3/covid-19/states/{states}
        return str(self.path / "schema-with-links.json")
