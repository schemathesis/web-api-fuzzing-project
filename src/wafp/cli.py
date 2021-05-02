import argparse
import sys
from typing import List, Optional, Type, TypeVar

T = TypeVar("T", bound="BaseCliArguments")


class BaseCliArguments:
    @classmethod
    def parse(cls: Type[T], args: Optional[List[str]] = None, *, catalog: Optional[str] = None) -> T:
        args = args or sys.argv[1:]
        parser = argparse.ArgumentParser()
        cls.add_arguments(parser, catalog=catalog)
        return cls.parse_args(args, parser)

    @classmethod
    def parse_args(cls: Type[T], args: List[str], parser: argparse.ArgumentParser) -> T:
        return cls(**vars(parser.parse_args(args)))  # type: ignore

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser, *, catalog: Optional[str] = None) -> None:
        return None
