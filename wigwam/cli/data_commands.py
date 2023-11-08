import argparse
from pathlib import Path

from ..data_commands import data_search
from ..defaults import default_workflowdata_path
from ._utils import help_formatter


def init_data_parsers(subparsers: argparse._SubParsersAction) -> None:
    """
    Augment an argument parser with setup commands.

    Parameters
    -------
    parser : argparse.ArgumentParser
        The parser to add setup commands to.
    """
    search_params = argparse.ArgumentParser(add_help=False)
    search_params.add_argument(
        "--data-file",
        "-f",
        type=Path,
        default=default_workflowdata_path(),
        metavar="FILENAME",
        help="The filename of the repository metadata file.",
    )
    search_params.add_argument(
        "--tags",
        "-t",
        nargs="+",
        action="append",
        default=[],
        metavar="TAG",
        help="A set of data repository tags. Can be used multiple times.",
    )
    search_params.add_argument(
        "--names",
        "-n",
        nargs="+",
        default=[],
        metavar="NAME",
        help="A set of data repository names.",
    )
    search_params.add_argument(
        "--all",
        "-a",
        action="store_true",
        default=False,
        help="If used, get all repositories. Other search parameters will be ignored.",
    )

    data_parser = subparsers.add_parser(
        "data", help="Perform data operations.", formatter_class=help_formatter
    )
    data_subparsers = data_parser.add_subparsers(dest="data_subcommand")

    search_parser = data_subparsers.add_parser(
        "search",
        parents=[search_params],
        help="Search a file for repository metadata.",
        formatter_class=help_formatter,
    )
    search_parser.add_argument(
        "--fields",
        nargs="+",
        default=[],
        metavar="FIELD",
        help="The metadata fields to be returned.",
    )


def run_data(args: argparse.Namespace) -> None:
    data_subcommand = args.data_subcommand
    del args.data_subcommand
    if data_subcommand == "search":
        data_search(**vars(args))
