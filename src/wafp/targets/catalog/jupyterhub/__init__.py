from typing import Dict

import requests

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
        return f"http://0.0.0.0:{self.port}/hub/api"

    def get_schema_location(self) -> str:
        return str(self.path / "schema.yaml")

    def is_ready(self, line: bytes) -> bool:
        return b"JupyterHub is now running at" in line

    def get_metadata(self) -> Metadata:
        return Metadata(
            language=Language.PYTHON,
            framework=Package(name="Tornado", version="6.1.0"),
            schema_source=SchemaSource(type=SchemaSourceType.STATIC, library=None),
            specification=Specification(name=SpecificationType.OPENAPI, version="2.0"),
            validation_from_schema=False,
        )

    def after_start(self, stdout: bytes, headers: Dict[str, str]) -> None:
        base_url = self.get_base_url()
        response = requests.post(f"{base_url}/authorizations/token", json={"username": "root", "password": "test"})
        token = response.json()["token"]
        headers["Authorization"] = f"token {token}"


class Linked(Default):
    def get_schema_location(self) -> str:
        # API schema with the following links:
        #  POST /users -> GET /users/{name}
        #  POST /users -> PATCH /users/{name}
        #  POST /users -> DELETE /users/{name}
        #  POST /users/{name} -> GET /users/{name}
        #  POST /users/{name} -> PATCH /users/{name}
        #  POST /users/{name} -> DELETE /users/{name}
        #  POST /users/{name} -> POST /users/{name}/activity
        #  POST /users/{name} -> POST /users/{name}/server
        #  POST /users/{name} -> DELETE /users/{name}/server
        #  POST /users/{name} -> POST /users/{name}/servers/{server_name}
        #  POST /users/{name} -> GET /users/{name}/tokens
        #  POST /users/{name} -> POST /users/{name}/tokens
        #  POST /users/{name}/servers/{server_name} -> DELETE /users/{name}/servers/{server_name}
        #  POST /users/{name}/tokens -> GET /users/{name}/tokens/{token_id}
        #  POST /users/{name}/tokens -> DELETE /users/{name}/tokens/{token_id}
        #  POST /groups/{name} -> GET /groups/{name}
        #  POST /groups/{name} -> DELETE /groups/{name}
        #  POST /groups/{name} -> POST /groups/{name}/users
        #  POST /groups/{name} -> DELETE /groups/{name}/users
        #  POST /authorizations/token -> GET /authorizations/token/{token}
        return str(self.path / "schema-with-links.json")
