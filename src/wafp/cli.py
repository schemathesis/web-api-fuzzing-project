import argparse
import sys
from typing import List, Optional, Type, TypeVar

T = TypeVar("T", bound="BaseCliArguments")


class BaseCliArguments:
    """A template for CLI arguments."""

    @classmethod
    def from_args(cls: Type[T], args: Optional[List[str]] = None, *, catalog: Optional[str] = None) -> T:
        """Convert input arguments into an instance of this class."""
        args = args or sys.argv[1:]
        parser = argparse.ArgumentParser()
        cls.extend_parser(parser, catalog=catalog)
        return cls.from_parser(args, parser)

    @classmethod
    def from_parser(cls: Type[T], args: List[str], parser: argparse.ArgumentParser) -> T:
        """Create an instance from args and parser."""
        return cls(**vars(parser.parse_args(args)))  # type: ignore

    @classmethod
    def extend_parser(cls, parser: argparse.ArgumentParser, *, catalog: Optional[str] = None) -> None:
        """Extend argument parser with custom arguments."""
        return None
