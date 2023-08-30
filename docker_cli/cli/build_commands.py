import argparse
from pathlib import Path
from typing import List

from ..commands import configure_cmake, copy_dir, get_archive
from ._utils import add_tag_argument, help_formatter


def init_build_parsers(subparsers: argparse._SubParsersAction) -> None:
    """
    Augment an argument parser with build commands.

    The build commands are the group of commands to be completed after the CUDA and
    conda environments have been installed to the image, with the purpose of acquiring
    and building the ISCE3 repository and any further repositories.
    These commands consist of the "get-archive", "copydir", and "cmake-config" commands,
    and more are being added.

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

    build_type_choices = ["Release", "Debug", "RelWithDebInfo", "MinSizeRel"]
    config_params = argparse.ArgumentParser(add_help=False)
    config_params.add_argument(
        "--build-type",
        type=str,
        default="Release",
        metavar="DCMAKE_BUILD_TYPE",
        choices=build_type_choices,
        help="The --DCMAKE_BUILD_TYPE argument for CMAKE. Valid options are: "
        + f"{', '.join(build_type_choices)}. Defaults to \"Release\".",
    )
    config_params.add_argument(
        "--no-cuda",
        action="store_true",
        default=False,
        help="If used, the build configuration will not use CUDA.",
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
    archive_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Run Docker build with no cache if used.",
    )

    copy_dir_parser = subparsers.add_parser(
        "copydir",
        parents=[setup_parse],
        help="Insert the contents of a directory at the given path.",
        formatter_class=help_formatter,
    )
    add_tag_argument(parser=copy_dir_parser, default="dir-copy")
    copy_dir_parser.add_argument(
        "--directory",
        "-d",
        type=Path,
        required=True,
        help="The directory to be copied to the image.",
    )
    copy_dir_parser.add_argument(
        "--target-path",
        "-p",
        type=Path,
        default=None,
        help="The path on the image to copy the source directory to. If not given, "
        "the base name of the path given by the directory argument will be used.",
    )
    copy_dir_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Run Docker build with no cache if used.",
    )

    config_parser = subparsers.add_parser(
        "cmake-config",
        parents=[setup_parse, config_params],
        help="Creates an image with a configured compiler.",
        formatter_class=help_formatter,
    )
    add_tag_argument(parser=config_parser, default="configured")
    config_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Run Docker build with no cache if used.",
    )


def build_command_names() -> List[str]:
    """Returns a list of all build command names."""
    return ["get-archive", "copydir", "cmake-config"]


def run_build(args: argparse.Namespace, command: str) -> None:
    if command == "get-archive":
        get_archive(**vars(args))
    if command == "copydir":
        copy_dir(**vars(args))
    if command == "cmake-config":
        configure_cmake(**vars(args))
