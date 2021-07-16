import re
from typing import Dict

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
        return str(self.path / "schema.yaml")

    def get_headers(self, line: bytes) -> Dict[str, str]:
        match = re.search(b"token=(.+)", line)
        if match is None:
            return {}
        token = match.groups()[0]
        return {"Authorization": f"token {token.decode()}"}

    def is_ready(self, line: bytes) -> bool:
        return b"?token=" in line

    def get_metadata(self) -> Metadata:
        return Metadata(
            language=Language.PYTHON,
            framework=Package(name="Tornado", version="6.1.0"),
            schema_source=SchemaSource(type=SchemaSourceType.STATIC, library=None),
            specification=Specification(name=SpecificationType.OPENAPI, version="2.0"),
            validation_from_schema=False,
        )


class Linked(Default):
    def get_schema_location(self) -> str:
        # API schema with the following links:
        #  PUT /api/contents/{path} -> POST /api/contents/{path}
        #  PUT /api/contents/{path} -> PATCH /api/contents/{path}
        #  PUT /api/contents/{path} -> DELETE /api/contents/{path}
        #  PUT /api/contents/{path} -> GET /api/contents/{path}
        #  PUT /api/contents/{path} -> POST /api/contents/{path}/checkpoints
        #  POST /api/contents/{path}/checkpoints -> POST /api/contents/{path}/checkpoints/{checkpoint_id}
        #  POST /api/contents/{path}/checkpoints -> DELETE /api/contents/{path}/checkpoints/{checkpoint_id}
        #  POST /api/sessions -> GET /api/sessions/{session}
        #  POST /api/sessions -> PATCH /api/sessions/{session}
        #  POST /api/sessions -> DELETE /api/sessions/{session}
        #  POST /api/kernels -> GET /api/kernels/{kernel_id}
        #  POST /api/kernels -> DELETE /api/kernels/{kernel_id}
        #  POST /api/kernels -> POST /api/kernels/{kernel_id}/interrupt
        #  POST /api/kernels -> POST /api/kernels/{kernel_id}/restart
        #  POST /api/terminals -> GET /api/terminals/{terminal_id}
        #  POST /api/terminals -> DELETE /api/terminals/{terminal_id}
        return str(self.path / "schema-with-links.json")
