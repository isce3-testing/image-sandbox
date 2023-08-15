import argparse
from pathlib import Path
from typing import List

from ..commands import get_archive
from ._utils import add_tag_argument, help_formatter


def init_build_parsers(subparsers: argparse._SubParsersAction) -> None:
    """
    Augment an argument parser with build commands.

    The build commands are the group of commands to be completed after the CUDA and
    conda environments have been installed to the image, with the purpose of acquiring
    and building the ISCE3 repository and any further repositories.
    These commands consist of the "get-archive" command, and more are being added.

    Parameters
    -----------
    parser : argparse.ArgumentParser
        The parser to add setup commands to.
    prefix : str
        The image tag prefix.
    """

    archive_params = argparse.ArgumentParser(add_help=False)
    archive_params.add_argument(
        "--archive-url",
        type=str,
        metavar="GIT_ARCHIVE",
        required=True,
        help='The URL of the Git archive to be fetched. Must be a "tar.gz" file.',
    )
    archive_params.add_argument(
        "--directory",
        type=Path,
        default=Path("/src"),
        help="The path to place the contents of the Git archive at on the image.",
    )

    setup_parse = argparse.ArgumentParser(add_help=False)
    setup_parse.add_argument(
        "--base",
        "-b",
        type=str,
        required=True,
        help="The name of the base Docker image.",
    )

    archive_parser = subparsers.add_parser(
        "get-archive",
        parents=[setup_parse, archive_params],
        help="Set up the GitHub repository image, in [USER]/[REPO_NAME] format.",
        formatter_class=help_formatter,
    )
    add_tag_argument(parser=archive_parser, default="repo")


def build_command_names() -> List[str]:
    """Returns a list of all build command names."""
    return ["get-archive"]


def run_build(args: argparse.Namespace, command: str) -> None:
    if command == "get-archive":
        get_archive(**vars(args))