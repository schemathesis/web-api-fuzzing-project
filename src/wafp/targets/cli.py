import argparse
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..cli import BaseCliArguments
from . import loader
from .core import BaseTarget, Target, unused_port


@dataclass
class SharedCliArguments(BaseCliArguments):
    target: str
    port: int
    no_cleanup: bool
    run_id: Optional[str]
    sentry_dsn: Optional[str]
    sentry_url: Optional[str]
    sentry_token: Optional[str]
    sentry_organization: Optional[str]
    sentry_project: Optional[str]

    def get_target_cls(self, *, catalog: Optional[str] = None) -> Target:
        cls = loader.by_name(self.target, catalog=catalog)
        if cls is None:
            raise ValueError(f"Target `{self.target}` is not found")
        return cls

    def get_target_kwargs(self) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {"port": self.port, "sentry_dsn": self.sentry_dsn}
        if self.run_id is not None:
            kwargs["run_id"] = self.run_id  # type: ignore
        return kwargs

    def get_target(self, *, catalog: Optional[str] = None) -> BaseTarget:
        cls = self.get_target_cls(catalog=catalog)
        return cls(**self.get_target_kwargs())

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser, *, catalog: Optional[str] = None) -> None:
        parser.add_argument(
            "target", choices=list(loader.get_all_variants(catalog=catalog)), help="Fuzz target to start"
        )
        parser.add_argument(
            "--port",
            required=False,
            type=int,
            default=unused_port(),
            help="TCP port on localhost used for the fuzz target",
        )
        parser.add_argument(
            "--no-cleanup",
            action="store_true",
            required=False,
            default=False,
            help="Do not perform any cleanup on exit",
        )
        parser.add_argument(
            "--run-id",
            action="store",
            type=str,
            required=False,
            help="Explicit ID used to identify different runs in Sentry",
        )
        parser.add_argument(
            "--sentry-dsn", action="store", type=str, required=False, help="Sentry DSN for the fuzz target"
        )
        parser.add_argument("--sentry-url", action="store", type=str, required=False, help="Sentry instance base URL")
        parser.add_argument("--sentry-token", action="store", type=str, required=False, help="Sentry access token")
        parser.add_argument(
            "--sentry-organization",
            action="store",
            type=str,
            required=False,
            help="The slug of the Sentry organization the fuzz target project belongs to",
        )
        parser.add_argument(
            "--sentry-project", action="store", type=str, required=False, help="The slug of the Sentry project"
        )


@dataclass
class CliArguments(SharedCliArguments):
    build: bool

    def get_target_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_target_kwargs()
        kwargs["force_build"] = self.build
        return kwargs

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser, *, catalog: Optional[str] = None) -> None:
        super().add_arguments(parser, catalog=catalog)
        parser.add_argument(
            "--build", action="store_true", required=False, default=False, help="Force building docker images"
        )
