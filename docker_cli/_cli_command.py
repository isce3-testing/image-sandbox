from __future__ import annotations

import argparse
from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple


# Use a custom help message formatter to improve readability by increasing the
# indentation of parameter descriptions to accommodate longer parameter names.
# This formatter also includes argument defaults automatically in the help string.
def help_formatter(prog):
    return argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=60)


class Command(ABC):
    def helpformat(prog):
        """The help formatter for this command."""
        return help_formatter(prog)

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the subcommand."""
        ...

    @abstractmethod
    def setup_parser(self, subparsers) -> argparse.ArgumentParser:
        """Create an argument parser for the subcommand."""
        ...

    @abstractmethod
    def run(self, args: argparse.Namespace | Dict[str, Any]) -> None:
        """Run the subcommand with the supplied arguments."""
        ...


# Abstract base class for all subcommands.
class BranchingCommand(Command):
    @property
    @abstractmethod
    def subcommand_dest(self) -> str:
        """The destination of the subcommand in argparse"""
        ...

    def pop_dest(
        self, args: argparse.Namespace | Dict[str, Any]
    ) -> Tuple[Dict[str, Any], str]:
        """
        Pops the subcommand destination argument from the argparse arguments and returns
        both it and the argument dict.

        Parameters
        ----------
        args : argparse.Namespace | Dict[str, Any]
            The argparse arguments in Namespace or dict format.

        Returns
        -------
        Dict[str, Any]
            The remaining argparse dictionary.
        subcommand : str
            The value that was held at the subcommand destination.
        """
        if isinstance(args, argparse.Namespace):
            kwds = vars(args)
        else:
            kwds = args
        dest_val: str = kwds.pop(self.subcommand_dest)
        assert isinstance(dest_val, str)

        return (kwds, dest_val)
