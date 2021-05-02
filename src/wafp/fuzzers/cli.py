import argparse
from dataclasses import dataclass
from typing import Dict, List, Optional, Type, TypeVar

from ..cli import BaseCliArguments
from ..utils import parse_headers
from . import loader
from .core import BaseFuzzer, Fuzzer

T = TypeVar("T", bound="SharedCliArguments")


@dataclass
class SharedCliArguments(BaseCliArguments):
    fuzzer: str
    headers: Optional[Dict[str, str]]

    @classmethod
    def parse_args(cls: Type[T], args: List[str], parser: argparse.ArgumentParser) -> T:
        kwargs = vars(parser.parse_args(args))
        if "headers" in kwargs:
            kwargs["headers"] = parse_headers(kwargs["headers"])
        return cls(**kwargs)

    def get_fuzzer_cls(self, *, catalog: Optional[str] = None) -> Fuzzer:
        cls = loader.by_name(self.fuzzer, catalog=catalog)
        if cls is None:
            raise ValueError(f"Fuzzer `{self.fuzzer}` is not found")
        return cls

    def get_fuzzer(self, *, catalog: Optional[str] = None) -> BaseFuzzer:
        return self.get_fuzzer_cls(catalog=catalog)()

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser, *, catalog: Optional[str] = None) -> None:
        parser.add_argument("fuzzer", choices=list(loader.get_all_variants(catalog=catalog)), help="Fuzzer to run")
        parser.add_argument(
            # Should be in form "NAME:VALUE"
            "--headers",
            "-H",
            type=str,
            action="extend",
            nargs="*",
        )


@dataclass
class CliArguments(SharedCliArguments):
    build: bool
    schema: str
    base_url: str

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser, *, catalog: Optional[str] = None) -> None:
        super().add_arguments(parser, catalog=catalog)
        parser.add_argument(
            "--build", action="store_true", required=False, default=False, help="Force building docker images"
        )
        parser.add_argument(
            "--schema",
            action="store",
            required=True,
            type=str,
        )
        parser.add_argument(
            "--base-url",
            action="store",
            required=True,
            type=str,
        )
