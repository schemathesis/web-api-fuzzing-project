import re
import time
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
        return f"http://0.0.0.0:{self.port}/v1"

    def get_schema_location(self) -> str:
        return f"http://0.0.0.0:{self.port}/v1/?format=openapi"

    def is_ready(self, line: bytes) -> bool:
        return b"Starting development server at" in line

    def get_metadata(self) -> Metadata:
        return Metadata(
            language=Language.PYTHON,
            framework=Package(name="Django", version="2.2.13"),
            schema_source=SchemaSource(
                type=SchemaSourceType.GENERATED, library=Package(name="drf-yasg", version="1.17.1")
            ),
            specification=Specification(name=SpecificationType.OPENAPI, version="2.0"),
        )

    def after_start(self, stdout: bytes, headers: Dict[str, str]) -> None:
        # Create auth token for the `Authorization` header
        base_url = self.get_base_url()
        credentials_response = requests.post(
            f"{base_url}/auth_tokens/register",
            json={"name": "test", "description": "TEST", "email": "test@test.com"},
        )
        data = credentials_response.json()
        response = requests.post(
            f"{base_url}/auth_tokens/token/",
            data={
                "client_id": data["client_id"],
                "client_secret": data["client_secret"],
                "grant_type": "client_credentials",
            },
        )
        token_data = response.json()
        token = token_data["access_token"]
        token_type = token_data["token_type"]
        headers["Authorization"] = f"{token_type} {token}"
        # Follow the link in the email to avoid throttling API requests
        deadline = time.time() + 10
        for line in self.compose.log_stream(deadline=deadline):
            match = re.search(f" ({base_url}/auth_tokens/verify/.+)$".encode(), line)
            if match is not None:
                token_verification_url = match.groups()[0].decode().strip()
                requests.get(token_verification_url)
                break
