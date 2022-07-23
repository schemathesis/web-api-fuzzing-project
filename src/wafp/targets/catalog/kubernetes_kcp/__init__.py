import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, TypedDict

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
KUBECONFIG_PATH = KCP_DATA_PATH / KUBECONFIG_FILENAME
ROOT_CLUSTER_ADMIN_USERNAME = "shard-admin"


@attr.s
class Default(BaseTarget):
    # TODO:
    # - proper cleanup of kcp_data folder
    #   and / or
    # - move etcd dump to targets artifacts folder after run ends

    fuzzer_skip_ssl_verify: bool = attr.ib(default=True)

    def get_base_url(self) -> str:
        # self.port does not work despite it was overridden in this child class, random came anyway
        # hardcode it for now
        return "https://0.0.0.0:6443"

    def get_schema_location(self) -> str:
        return f"{self.get_base_url()}/openapi/v2"

    def get_environment_variables(self) -> Dict[str, str]:
        env = super().get_environment_variables()
        env.update({"UID": f"{os.getuid()}", "GID": f"{os.getgid()}"})
        return env

    def is_ready(self, line: bytes) -> bool:
        return b"Bootstrapped Namespace root|default" in line

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

    def before_start(self) -> None:
        # TODO add logging if smth goes wrong
        shutil.rmtree(KCP_DATA_PATH, ignore_errors=True)

    def after_start(self, stdout: bytes, headers: Dict[str, str]) -> None:
        user_token = read_user_token()
        if user_token is None:
            raise RuntimeError(f"Failed to find access token for user `{ROOT_CLUSTER_ADMIN_USERNAME}`")
        headers["Authorization"] = f"Bearer {user_token}"


def read_user_token(path: Path = KUBECONFIG_PATH) -> Optional[str]:
    with path.open() as fd:
        kubeconfig = yaml.safe_load(fd)
    return extract_user_token(kubeconfig)


class UserData(TypedDict):
    token: str


class User(TypedDict):
    name: str
    user: UserData


class KubeConfig(TypedDict):
    users: List[User]


def extract_user_token(kubeconfig: KubeConfig, username: str = ROOT_CLUSTER_ADMIN_USERNAME) -> Optional[str]:
    """Extract the admin's token from kubeconfig file."""
    if not isinstance(kubeconfig, dict):
        raise ValueError(f"Invalid `{KUBECONFIG_FILENAME}` content: {kubeconfig!r}")
    try:
        for user in kubeconfig["users"]:
            if user["name"] == username:
                return user["user"]["token"]
    except KeyError:
        return None
    return None
