import argparse
from typing import List

from ..commands import clone
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
    clone_params = argparse.ArgumentParser(add_help=False)
    clone_params.add_argument(
        "--repo",
        type=str,
        metavar="GIT_REPO",
        default="isce-framework/isce3",
        help="The name of the GitHub repository to be installed. "
        'Default: "isce-framework/isce3"',
    )
    # This argument currently disabled as this code does not presently support git
    # branches. For consideration on this topic, see _docker_git.py in the parent folder
    """clone_params.add_argument(
        "--branch", type=str, metavar="REPO_BRANCH", default="",
        help="The name of the branch to checkout. Defaults to \"\"."
    )"""

    setup_parse = argparse.ArgumentParser(add_help=False)
    setup_parse.add_argument(
        "--base",
        "-b",
        type=str,
        required=True,
        help="The name of the base Docker image.",
    )

    clone_parser = subparsers.add_parser(
        "clone",
        parents=[setup_parse, clone_params],
        help="Set up the GitHub repository image, in [USER]/[REPO_NAME] format.",
        formatter_class=help_formatter,
    )
    add_tag_argument(parser=clone_parser, default="repo")


def build_command_names() -> List[str]:
    """Returns a list of all build command names."""
    return ["clone"]


def run_build(args: argparse.Namespace, command: str) -> None:
    if command == "clone":
        clone(**vars(args))
