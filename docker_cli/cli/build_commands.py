import argparse
from pathlib import Path
from typing import List

from ..commands import get_archive
from ._utils import add_tag_argument, help_formatter


def init_build_parsers(subparsers: argparse._SubParsersAction) -> None:
    """
    Augment an argument parser with build commands.

    Parameters
    -------
    parser : argparse.ArgumentParser
        The parser to add setup commands to.
    prefix : str
        The image tag prefix.
    """
    isce3_github = "https://github.com/isce-framework/isce3"

    clone_params = argparse.ArgumentParser(add_help=False)
    clone_params.add_argument(
        "--archive-url",
        type=str,
        metavar="GIT_ARCHIVE",
        default=f"{isce3_github}/archive/refs/tags/v0.14.0.tar.gz",
        help='The URL of the Git archive to be fetched. Must be a "tar.gz" file.',
    )
    clone_params.add_argument(
        "--folder-path",
        type=Path,
        metavar="FOLDER_PATH",
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

    clone_parser = subparsers.add_parser(
        "get-archive",
        parents=[setup_parse, clone_params],
        help="Set up the GitHub repository image, in [USER]/[REPO_NAME] format.",
        formatter_class=help_formatter,
    )
    add_tag_argument(parser=clone_parser, default="repo")


def build_command_names() -> List[str]:
    """Returns a list of all build command names."""
    return ["get-archive"]


def run_build(args: argparse.Namespace, command: str) -> None:
    if command == "get-archive":
        get_archive(**vars(args))
