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
        )

    def after_start(self, stdout: bytes, headers: Dict[str, str]) -> None:
        base_url = self.get_base_url()
        response = requests.post(f"{base_url}/authorizations/token", json={"username": "root", "password": "test"})
        token = response.json()["token"]
        headers["Authorization"] = f"token {token}"
