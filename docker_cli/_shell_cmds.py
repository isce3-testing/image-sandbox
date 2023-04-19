import os
from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional, Type, Union


class PackageManager(ABC):
    """
    A Linux package panager

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
    def generate_install_command(
            targets: Iterable[str],
            *,
            stringify: bool = False,
            clean: bool = True
    ) -> Union[List[str], str]:
        """
        Returns an set of commands to install the targets.

        Parameters
        ----------
        targets : Sequence[str]
            The install targets.
        stringify : bool, optional
            Whether to return a string or list - if true, will return a string.
            Defaults to False.
        clean : bool, optional
            Whether or not to add a clean command to the list.
            Defaults to True.

        Returns
        -------
        Union[List[str], str]
            The commands.
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def generate_package_command(
            target: str,
            *,
            stringify: bool = False
    ) -> Union[List[str], str]:
        """
        Returns a command to install a single package.

        Uses the package tool underlying the package manager if one is
        available. (e.g. dpkg or rpm)

        Parameters
        ----------
        target : str
            The install target.
        stringify : bool, optional
            Whether to return a string or list - if true, will return a string.
            Defaults to False.

        Returns
        -------
        Union[List[str], str]
            The commands.
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def generate_configure_command(
            *,
            stringify: bool = False
    ) -> Union[List[str], str]:
        """
        Returns commands to configure and update the package manager.

        Parameters
        ----------
        stringify : bool, optional
            Whether to return a string or list - if true, will return a string.
            Defaults to False.

        Returns
        -------
        Union[List[str], str]
            The commands.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def name(self):
        """
        The package manager's command name.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def file_type(self):
        """
        The filetype associated with this package manager.
        """
        raise NotImplementedError()


class Yum(PackageManager):

    @staticmethod
    def generate_install_command(
            targets: Iterable[str],
            *,
            stringify: bool = False,
            clean: bool = True,
    ) -> Union[List[str], str]:
        retval = []
        retval += ["yum", "install", "-y"]
        retval.extend(targets)
        if clean:
            retval += ["&&", "yum", "clean", "all"]
            retval += ["&&", "rm", "-rf", "/var/cache/yum"]
        if stringify:
            return ' '.join(retval)
        return retval  # pragma: no cover

    @staticmethod
    def generate_package_command(  # pragma: no cover
            target: str,
            *,
            stringify: bool = False
    ) -> Union[List[str], str]:
        retval = ["rpm", "-i", target]
        if stringify:
            return ' '.join(retval)
        return retval

    @staticmethod
    def generate_configure_command(
            *,
            stringify: bool = False
    ) -> Union[List[str], str]:
        retval = []
        retval += ["yum", "update", "-y"]
        retval += ["&&", "echo", "'skip_missing_names_on_install=False'"]
        retval += [">>", "/etc/yum.conf"]
        retval += ["&&", "rm", "-rf", "/var/cache/yum"]
        if stringify:
            return ' '.join(retval)
        return retval  # pragma: no cover

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
            *,
            stringify: bool = False,
            clean: bool = True,
    ) -> Union[List[str], str]:
        retval = []
        retval += ["apt-get", "-y", "update", "&&"]
        retval += ["apt-get", "-y", "install"]
        retval.extend(targets)
        if clean:
            retval += ["&&", "apt-get", "clean", "all"]
        if stringify:
            return ' '.join(retval)
        return retval  # pragma: no cover

    @staticmethod
    def generate_package_command(  # pragma: no cover
            target: str,
            *,
            stringify: bool = False
    ) -> Union[List[str], str]:
        retval = ["dpkg", "-i", target]
        if stringify:
            return ' '.join(retval)
        return retval

    @staticmethod
    def generate_configure_command(
            *,
            stringify: bool = False
    ) -> Union[List[str], str]:
        retval = []
        retval += ["apt-get", "-y", "update"]
        retval += ["&&", "apt-get", "clean", "all"]
        if stringify:
            return ' '.join(retval)
        return retval  # pragma: no cover

    @property
    def name(self):
        return "apt-get"

    @property
    def file_type(self):  # pragma: no cover
        return "deb"


class URLReader(ABC):
    """
    A program that accesses URLs.

    Examples of such programs are cURL and wget.
    Capabilities include:
    -   Generating a command to access a URL via
            :func:`~docker_cli.URLReader.generate_read_command`
    -   Returning the name of the program.
    """

    @staticmethod
    @abstractmethod
    def generate_read_command(
        target: str,
        *,
        output_target: Optional[Union[str, os.PathLike[str]]] = None,
        stringify: bool = False
    ) -> Union[List[str], str]:
        """
        Returns a set of commands to read a URL.

        Parameters
        ----------
        target : str
            The target URL.
        output_target : os.PathLike, optional
            The file to redirect the URL contents to. If None, the URL contents
            will go to stdout. Defaults to None.
        stringify : bool, optional
            Whether to return a string or list - if true, will return a string.
            Defaults to False.

        Returns
        -------
        Union[List[str], str]
            The commands.
        """
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def get_name() -> str:
        """
        Returns the name of the command.

        Returns
        -------
        str
            The command name.
        """
        raise NotImplementedError()


class Wget(URLReader):

    @staticmethod
    def generate_read_command(
            target: str,
            *,
            output_target: Optional[Union[os.PathLike[str], str]] = None,
            stringify: bool = False
    ) -> Union[List[str], str]:
        retval = ["wget", target]
        if output_target is not None:
            retval += ["-O", str(output_target)]
        if stringify:
            return ' '.join(retval)
        return retval  # pragma: no cover

    @staticmethod
    def get_name() -> str:  # pragma: no cover
        return "wget"


class cURL(URLReader):

    @staticmethod
    def generate_read_command(
            target: str,
            *,
            output_target: Optional[Union[os.PathLike[str], str]] = None,
            stringify: bool = False
    ) -> Union[List[str], str]:
        retval = ["curl", "--ssl", target]
        if output_target is not None:
            retval += ["-o", str(output_target)]
        if stringify:
            return ' '.join(retval)
        return retval  # pragma: no cover

    @staticmethod
    def get_name() -> str:  # pragma: no cover
        return "curl"


def get_package_manager(name: str) -> PackageManager:
    """
    Returns the PackageManager associated with a name.

    Parameters
    ----------
    name : str
        The name of the command

    Returns
    -------
    PackageManager
        An associated PackageManager object

    Raises
    ------
    ValueError
        When `name` does not correspond to a supported package manager.
    """
    name_cleaned = name.lower()
    if name_cleaned == "apt-get":
        return AptGet()
    if name_cleaned == "yum":
        return Yum()
    else:
        raise ValueError(f"Package manager '{name}' not recognized!")


def get_url_reader(name: str) -> Type[URLReader]:
    """
    Returns the URLReader associated with a command name.

    Parameters
    ----------
    name : str
        The command name.

    Returns
    -------
    URLReader
        The associated URLReader class

    Raises
    ------
    ValueError
        When `name` does not correspond to a supported URL reader.
    """
    url_readers: Dict[str, Type[URLReader]] = {
        "curl": cURL,
        "wget": Wget
    }
    if name in url_readers.keys():
        url_reader: Type[URLReader] = url_readers[name]
        return url_reader
    else:
        raise ValueError(f"URL Reader {name} not recognized!")


def get_supported_package_managers() -> List[str]:
    """
    Returns a list of supported package managers.

    Returns
    -------
    List[str]
        The list.
    """
    return [
        "yum",
        "apt-get"
    ]


def get_supported_url_readers() -> List[str]:
    """
    Returns a list of supported URL readers.

    Returns
    -------
    List[str]
        The list.
    """
    return [
        "curl",
        "wget"
    ]
