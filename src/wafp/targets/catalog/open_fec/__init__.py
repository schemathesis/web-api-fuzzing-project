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


class Linked(Default):
    def get_schema_location(self) -> str:
        # API schema with the following links:
        #  GET /candidates/ -> GET /candidate/{candidate_id}/totals/
        #  GET /candidates/ -> GET /candidate/{candidate_id}/history/{cycle}/
        #  GET /candidates/ -> GET /candidate/{candidate_id}/history/
        #  GET /candidates/ -> GET /candidate/{candidate_id}/filings/
        #  GET /candidates/ -> GET /candidate/{candidate_id}/committees/history/{cycle}/
        #  GET /candidates/ -> GET /candidate/{candidate_id}/committees/history/
        #  GET /candidates/ -> GET /candidate/{candidate_id}/committees/
        #  GET /candidates/ -> GET /candidate/{candidate_id}/
        #  GET /committees/ -> GET /committee/{committee_id}/totals/
        #  GET /committees/ -> GET /committee/{committee_id}/reports/
        #  GET /committees/ -> GET /committee/{committee_id}/history/{cycle}/
        #  GET /committees/ -> GET /committee/{committee_id}/history/
        #  GET /committees/ -> GET /committee/{committee_id}/filings/
        #  GET /committees/ -> GET /committee/{committee_id}/candidates/history/{cycle}/
        #  GET /committees/ -> GET /committee/{committee_id}/candidates/history/
        #  GET /committees/ -> GET /committee/{committee_id}/candidates/
        #  GET /committees/ -> GET /committee/{committee_id}/
        return str(self.path / "schema-with-links.json")
