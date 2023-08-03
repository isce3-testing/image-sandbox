import argparse
import sys
from typing import Sequence

from .._utils import universal_tag_prefix
from ._utils import help_formatter
from .setup_commands import init_setup_parsers, run_setup
from .util_commands import init_util_parsers, run_util


def initialize_parser() -> argparse.ArgumentParser:
    """
    Create a top-level argument parser.

    Returns
    -------
    argparse.ArgumentParser
        The parser.
    """
    prefix = universal_tag_prefix()

    parser = argparse.ArgumentParser(prog=__package__, formatter_class=help_formatter)

    # Add arguments
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_setup_parsers(subparsers, prefix)
    init_util_parsers(subparsers, prefix)

    return parser


def main(args: Sequence[str] = sys.argv[1:]):
    parser = initialize_parser()
    args_parsed = parser.parse_args(args)
    command: str = args_parsed.command
    del args_parsed.command
    if command == "setup":
        run_setup(args_parsed)
    else:
        run_util(args_parsed, command)
