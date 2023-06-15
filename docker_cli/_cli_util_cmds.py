from __future__ import annotations

import argparse
from typing import Any, Dict

from ._cli_command import Command
from ._utils import universal_tag_prefix
from .commands import dropin, remove


class DropInCommand(Command):
    """The argparse command for drop-in sessions."""

    @property
    def name(self) -> str:
        return "dropin"

    def setup_parser(
        self, subparsers: argparse._SubParsersAction
    ) -> argparse.ArgumentParser:
        parser: argparse.ArgumentParser = subparsers.add_parser(
            self.name,
            help="Start a drop-in session.",
            formatter_class=self.helpformat(),
        )

        parser.add_argument(
            "tag",
            metavar="IMAGE_TAG",
            type=str,
            help="The tag or ID of the desired image.",
        )

        return parser

    def run(self, args: argparse.Namespace | Dict[str, Any]) -> None:
        if isinstance(args, argparse.Namespace):
            kwds = vars(args)
        else:
            kwds = args
        dropin(**kwds)


class RemoveCommand(Command):
    """The argparse command for image removal."""

    @property
    def name(self) -> str:
        return "remove"

    def setup_parser(
        self, subparsers: argparse._SubParsersAction
    ) -> argparse.ArgumentParser:
        prefix = universal_tag_prefix()

        parser: argparse.ArgumentParser = subparsers.add_parser(
            "remove",
            help=(
                f"Remove all docker images beginning with {prefix}-[IMAGE_TAG] for each"
                " image tag provided."
            ),
            formatter_class=self.helpformat(),
        )

        parser.add_argument(
            "tags",
            metavar="IMAGE_TAG",
            type=str,
            nargs="+",
            help=(
                f"An image tag or wildcard. Will be prefixed with {prefix} if not"
                " already prefixed."
            ),
        )
        parser.add_argument(
            "--force",
            "-f",
            action="store_true",
            help="Force the image removal.",
        )
        parser.add_argument(
            "--quiet",
            "-q",
            action="store_true",
            help="Run the removal quietly.",
        )
        parser.add_argument(
            "--ignore-prefix",
            action="store_true",
            help=(
                f"Ignore the {prefix} prefix. CAUTION: Using wildcards with this"
                " argument can result in unintended removal of docker images. Use with"
                " caution."
            ),
        )

        return parser

    def run(self, args: argparse.Namespace | Dict[str, Any]) -> None:
        if isinstance(args, argparse.Namespace):
            kwds = vars(args)
        else:
            kwds = args

        remove(**kwds)
