import re
from typing import Dict

from wafp.targets import (
    BaseTarget,
    Language,
    Metadata,
    SchemaSource,
    SchemaSourceType,
    Specification,
    SpecificationType,
)


class Default(BaseTarget):
    def get_base_url(self) -> str:
        return f"http://0.0.0.0:{self.port}/"

    def get_schema_location(self) -> str:
        return str(self.path / "schema.yaml")

    def get_headers(self, line: bytes) -> Dict[str, str]:
        match = re.search(b"token: (.+)$", line)
        if match is None:
            return {}
        token = match.groups()[0]
        return {"Authorization": token.decode()}

    def is_ready(self, line: bytes) -> bool:
        return b"token: " in line

    def get_metadata(self) -> Metadata:
        return Metadata(
            language=Language.GO,
            framework=None,
            schema_source=SchemaSource(type=SchemaSourceType.STATIC, library=None),
            specification=Specification(name=SpecificationType.OPENAPI, version="2.0"),
            validation_from_schema=False,
        )


class Linked(Default):
    def get_schema_location(self) -> str:
        # API schema with the following links:
        #  POST /api/baskets/{name} -> POST /api/baskets/{name}
        #  POST /api/baskets/{name} -> GET /api/baskets/{name}
        #  POST /api/baskets/{name} -> PUT /api/baskets/{name}
        #  POST /api/baskets/{name} -> DELETE /api/baskets/{name}
        #  POST /api/baskets/{name} -> GET /api/baskets/{name}/responses/{method}
        #  POST /api/baskets/{name} -> PUT /api/baskets/{name}/responses/{method}
        #  POST /api/baskets/{name} -> GET /api/baskets/{name}/requests
        #  POST /api/baskets/{name} -> DELETE /api/baskets/{name}/requests
        #  GET /api/baskets/{name} -> POST /api/baskets/{name}
        #  GET /api/baskets/{name} -> GET /api/baskets/{name}
        #  GET /api/baskets/{name} -> PUT /api/baskets/{name}
        #  GET /api/baskets/{name} -> DELETE /api/baskets/{name}
        #  GET /api/baskets/{name} -> GET /api/baskets/{name}/responses/{method}
        #  GET /api/baskets/{name} -> PUT /api/baskets/{name}/responses/{method}
        #  GET /api/baskets/{name} -> GET /api/baskets/{name}/requests
        #  GET /api/baskets/{name} -> DELETE /api/baskets/{name}/requests
        #  PUT /api/baskets/{name} -> POST /api/baskets/{name}
        #  PUT /api/baskets/{name} -> GET /api/baskets/{name}
        #  PUT /api/baskets/{name} -> PUT /api/baskets/{name}
        #  PUT /api/baskets/{name} -> DELETE /api/baskets/{name}
        #  PUT /api/baskets/{name} -> GET /api/baskets/{name}/responses/{method}
        #  PUT /api/baskets/{name} -> PUT /api/baskets/{name}/responses/{method}
        #  PUT /api/baskets/{name} -> GET /api/baskets/{name}/requests
        #  PUT /api/baskets/{name} -> DELETE /api/baskets/{name}/requests
        #  DELETE /api/baskets/{name} -> POST /api/baskets/{name}
        #  DELETE /api/baskets/{name} -> GET /api/baskets/{name}
        #  DELETE /api/baskets/{name} -> PUT /api/baskets/{name}
        #  DELETE /api/baskets/{name} -> DELETE /api/baskets/{name}
        #  DELETE /api/baskets/{name} -> GET /api/baskets/{name}/responses/{method}
        #  DELETE /api/baskets/{name} -> PUT /api/baskets/{name}/responses/{method}
        #  DELETE /api/baskets/{name} -> GET /api/baskets/{name}/requests
        #  DELETE /api/baskets/{name} -> DELETE /api/baskets/{name}/requests
        #  GET /api/baskets/{name}/responses/{method} -> POST /api/baskets/{name}
        #  GET /api/baskets/{name}/responses/{method} -> GET /api/baskets/{name}
        #  GET /api/baskets/{name}/responses/{method} -> PUT /api/baskets/{name}
        #  GET /api/baskets/{name}/responses/{method} -> DELETE /api/baskets/{name}
        #  GET /api/baskets/{name}/responses/{method} -> GET /api/baskets/{name}/responses/{method}
        #  GET /api/baskets/{name}/responses/{method} -> PUT /api/baskets/{name}/responses/{method}
        #  GET /api/baskets/{name}/responses/{method} -> GET /api/baskets/{name}/requests
        #  GET /api/baskets/{name}/responses/{method} -> DELETE /api/baskets/{name}/requests
        #  PUT /api/baskets/{name}/responses/{method} -> POST /api/baskets/{name}
        #  PUT /api/baskets/{name}/responses/{method} -> GET /api/baskets/{name}
        #  PUT /api/baskets/{name}/responses/{method} -> PUT /api/baskets/{name}
        #  PUT /api/baskets/{name}/responses/{method} -> DELETE /api/baskets/{name}
        #  PUT /api/baskets/{name}/responses/{method} -> GET /api/baskets/{name}/responses/{method}
        #  PUT /api/baskets/{name}/responses/{method} -> PUT /api/baskets/{name}/responses/{method}
        #  PUT /api/baskets/{name}/responses/{method} -> GET /api/baskets/{name}/requests
        #  PUT /api/baskets/{name}/responses/{method} -> DELETE /api/baskets/{name}/requests
        #  GET /api/baskets/{name}/requests -> POST /api/baskets/{name}
        #  GET /api/baskets/{name}/requests -> GET /api/baskets/{name}
        #  GET /api/baskets/{name}/requests -> PUT /api/baskets/{name}
        #  GET /api/baskets/{name}/requests -> DELETE /api/baskets/{name}
        #  GET /api/baskets/{name}/requests -> GET /api/baskets/{name}/responses/{method}
        #  GET /api/baskets/{name}/requests -> PUT /api/baskets/{name}/responses/{method}
        #  GET /api/baskets/{name}/requests -> GET /api/baskets/{name}/requests
        #  GET /api/baskets/{name}/requests -> DELETE /api/baskets/{name}/requests
        #  DELETE /api/baskets/{name}/requests -> POST /api/baskets/{name}
        #  DELETE /api/baskets/{name}/requests -> GET /api/baskets/{name}
        #  DELETE /api/baskets/{name}/requests -> PUT /api/baskets/{name}
        #  DELETE /api/baskets/{name}/requests -> DELETE /api/baskets/{name}
        #  DELETE /api/baskets/{name}/requests -> GET /api/baskets/{name}/responses/{method}
        #  DELETE /api/baskets/{name}/requests -> PUT /api/baskets/{name}/responses/{method}
        #  DELETE /api/baskets/{name}/requests -> GET /api/baskets/{name}/requests
        #  DELETE /api/baskets/{name}/requests -> DELETE /api/baskets/{name}/requests
        return str(self.path / "schema-with-links.yaml")
