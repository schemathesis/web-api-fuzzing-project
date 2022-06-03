import os
from functools import cached_property
from pathlib import Path
from typing import Dict

import attr
import yaml

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

KUBECONFIG_FILENAME = "admin.kubeconfig"
KCP_DATA_PATH = Path(__file__).parent.absolute() / "kcp_data" / ".kcp"


@attr.s
class Default(BaseTarget):
    # TODO:
    # - proper cleanup of kcp_data folder
    #   and / or
    # - move etcd dump to targets artifacts folder after run ends

    # port: int = attr.field(factory=lambda: 6443)
    fuzzer_skip_ssl_verify: bool = attr.ib(default=True)

    def get_base_url(self) -> str:
        # self.port does not work despite it was overrided in this child class, random came anyway
        # hardcode it for now
        return "https://0.0.0.0:6443"

    def get_schema_location(self) -> str:
        return f"{self.get_base_url()}/openapi/v2"

    def get_environment_variables(self):
        env = super().get_environment_variables()
        env.update({
            "UID": f"{os.getuid()}",
            "GID": f"{os.getgid()}"
        })
        return env

    def is_ready(self, line: bytes) -> bool:
        return b"Reconciling namespace root|default" in line

    def get_metadata(self) -> Metadata:
        return Metadata(
            language=Language.GO,
            framework=Package(name="kubernetes", version="1.23.5"),
            schema_source=SchemaSource(
                type=SchemaSourceType.GENERATED, library=Package(name="kubebuilder", version="unknown")
            ),
            validation_from_schema=True,
            specification=Specification(name=SpecificationType.OPENAPI, version="2.0"),
        )

    def after_start(self, stdout: bytes, headers: Dict[str, str]) -> None:
        headers["Authorization"] = f"Bearer {self.auth_token}"

    @cached_property
    def auth_token(self) -> str:
        with open(KCP_DATA_PATH / KUBECONFIG_FILENAME, "r") as fd:
            kubeconfig = fd.read()
        kubeconfig = yaml.safe_load(kubeconfig)
        # TODO look up for kubeconfig type
        token: str = kubeconfig["users"][0]["user"]["token"]  # type: ignore
        return token
