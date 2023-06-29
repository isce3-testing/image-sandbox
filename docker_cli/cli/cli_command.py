from __future__ import annotations

import argparse
from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple


class Command(ABC):
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
        remaining_dict : Dict[str, Any]
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
