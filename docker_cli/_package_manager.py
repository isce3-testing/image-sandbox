import shlex
import textwrap
from abc import ABC, abstractmethod
from typing import Iterable, List


class PackageManager(ABC):
    """
    A Linux package manager

    Capabilities include:
    -   Providing string for generating installation and configuration of
        packages on the command line via:
    \t  -   :func:`~docker_cli.PackageManager.generate_install_command`
    \t  -   :func:`~docker_cli.PackageManager.generate_package_command`
    \t  -   :func:`~docker_cli.PackageManager.generate_configure_command`
    -   Returning an associated name and filetype
    """

    @staticmethod
    @abstractmethod
    def generate_install_command(targets: Iterable[str], *, clean: bool = True) -> str:
        """
        Returns an set of commands to install a list of target packages.

        Parameters
        ----------
        targets : Iterable[str]
            The install targets.
        clean : bool, optional
            Whether or not to add a clean command to the list.
            Defaults to True.

        Returns
        -------
        Union[List[str], str]
            The commands.
        """
        ...

    @staticmethod
    @abstractmethod
    def generate_package_command(
        target: str,
    ) -> str:
        """
        Returns a command to install a single package.

        Uses the package tool underlying the package manager if one is
        available. (e.g. dpkg or rpm)

        Parameters
        ----------
        target : str
            The install target.

        Returns
        -------
        Union[List[str], str]
            The commands.
        """
        ...

    @staticmethod
    @abstractmethod
    def generate_configure_command() -> str:
        """
        Returns commands to configure and update the package manager.

        Returns
        -------
        Union[List[str], str]
            The commands.
        """
        ...

    @property
    @abstractmethod
    def name(self):
        """
        The package manager's command name.
        """
        ...

    @property
    @abstractmethod
    def file_type(self):
        """
        The file extension of package files associated with this package manager.
        """
        ...


class Yum(PackageManager):
    @staticmethod
    def generate_install_command(
        targets: Iterable[str],
        clean: bool = True,
    ) -> str:
        retval = ["yum", "install", "-y"]
        retval.extend(targets)
        if clean:
            retval += ["&&", "yum", "clean", "all"]
            retval += ["&&", "rm", "-rf", "/var/cache/yum"]
        return " ".join(retval)

    @staticmethod
    def generate_package_command(  # pragma: no cover
        target: str,
    ) -> str:
        retval = ["rpm", "-i", target]
        return shlex.join(retval)

    @staticmethod
    def generate_configure_command() -> str:
        retval = textwrap.dedent(
            """
            yum update -y                                                       \\
              && echo 'skip_missing_names_on_install=False' >> /etc/yum.conf    \\
              && rm -rf /var/cache/yum
        """
        ).strip()
        return retval

    @property
    def name(self):
        return "yum"

    @property
    def file_type(self):  # pragma: no cover
        return "rpm"


class AptGet(PackageManager):
    @staticmethod
    def generate_install_command(
        targets: Iterable[str],
        clean: bool = True,
    ) -> str:
        retval = ["apt-get", "-y", "update", "&&"]
        retval += ["apt-get", "-y", "install"]
        retval.extend(targets)
        if clean:
            retval += ["&&", "apt-get", "clean", "all"]
        return " ".join(retval)

    @staticmethod
    def generate_package_command(  # pragma: no cover
        target: str,
    ) -> str:
        retval = ["dpkg", "-i", target]
        return shlex.join(retval)

    @staticmethod
    def generate_configure_command() -> str:
        retval = ["apt-get", "-y", "update"]
        retval += ["&&", "apt-get", "clean", "all"]
        return " ".join(retval)

    @property
    def name(self):
        return "apt-get"

    @property
    def file_type(self):  # pragma: no cover
        return "deb"


def get_package_manager(name: str) -> PackageManager:
    """
    Returns the PackageManager associated with a name.

    Parameters
    ----------
    name : str
        The name of the command.

    Returns
    -------
    PackageManager
        An associated PackageManager object.

    Raises
    ------
    ValueError
        When `name` does not correspond to a supported package manager.
    """
    if name == "apt-get":
        return AptGet()
    if name == "yum":
        return Yum()
    else:
        raise ValueError(f"Package manager '{name}' not recognized!")


def get_supported_package_managers() -> List[str]:
    """
    Returns a list of supported package managers.

    Returns
    -------
    List[str]
        The list.
    """
    return ["yum", "apt-get"]
