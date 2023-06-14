import io
import random
import re
from shlex import split
from string import ascii_lowercase, digits
from subprocess import DEVNULL, CalledProcessError, run
from threading import Lock
from typing import Optional, Tuple, Type

from ._image import Image
from ._shell_cmds import (
    PackageManager,
    URLReader,
    get_package_manager,
    get_supported_package_managers,
    get_supported_url_readers,
    get_url_reader,
)


def universal_tag_prefix() -> str:
    """
    Returns a prefix for tags generated by the system.

    Returns
    -------
    str
        The prefix.
    """
    return "dcli"


def _package_manager_check(image: Image) -> PackageManager:
    """
    Returns the package manager present on an image.

    Parameters
    ----------
    base : Image
        The image.

    Returns
    -------
    PackageManager
        The package manager.
    """
    package_mgrs = image.check_command_availability(get_supported_package_managers())

    if package_mgrs:
        package_mgr = get_package_manager(package_mgrs[0])
    else:
        ValueError("No recognized package manager found on parent image.")

    return package_mgr


def _url_reader_check(
    image: Image, package_mgr: PackageManager
) -> Tuple[Type[URLReader], str]:
    """
    Return the URL reader on a given image, and a string to install one if there is
    none.

    Parameters
    ----------
    base : Image
        The image.
    package_mgr : PackageManager
        The images package manager.

    Returns
    -------
    Tuple[Type[URLReader], str]
        The installed URL reader and a string to install it if necessary.
    """
    url_programs = image.check_command_availability(get_supported_url_readers())
    init_lines = ""
    if url_programs:
        url_program: Type[URLReader] = get_url_reader(url_programs[0])
    else:
        init_lines += (
            "RUN "
            + str(
                package_mgr.generate_install_command(targets=["wget"], stringify=True)
            )
            + "\n"
        )
        url_program = get_url_reader("wget")

    return url_program, init_lines


def _image_command_check(
    image_name: str,
    configure: bool = False,
    stdout: Optional[io.TextIOBase] = None,
    stderr: Optional[io.TextIOBase] = None,
) -> Tuple[PackageManager, Type[URLReader], str]:
    """
    Determine what relevant commands are present on the image.

    Determines what package manager and URL reader are on the image, and
    returns a set of initial lines to install a URL reader if none is present.

    Parameters
    ----------
    image_name : str
        The tag or ID by which the image can be found
    configure : bool
        Add configuration commands to the returned string if True. Defaults to False.
    stdout : io.TextIOBase, optional
        A file-like object to redirect stdout to. If None, no redirection will
        occur. By default None
    stderr : io.TextIOBase, optional
        A file-like object to redirect stderr to. If None, no redirection will
        occur. By default None

    Returns
    -------
    Tuple[PackageManager, URLReader, str]
        The Package Manager object, URL Reader object, and any install and
        configuration lines required by the dockerfile.

    Raises
    ------
    ValueError
        If the parent image does not have a recognized package manager.
    """

    tag = f"{universal_tag_prefix()}-temp-{UniqueGenerator.generate(k=10)}"
    try:
        base: Image = Image.build(  # type: ignore
            tag=tag,
            dockerfile_string=f"FROM {image_name}\nRUN mkdir {tag}",
            stdout=stdout,
            stderr=stderr,
        )
    except CalledProcessError:
        raise ValueError(f"Image not found: {image_name}")

    package_mgr = _package_manager_check(image=base)

    if configure:
        init_lines: str = (
            "RUN " + str(package_mgr.generate_configure_command(stringify=True)) + "\n"
        )
    else:
        init_lines = ""

    url_program, url_init = _url_reader_check(image=base, package_mgr=package_mgr)
    init_lines += url_init

    run(split(f"docker image rm {tag}"), stdout=DEVNULL, stderr=DEVNULL)

    return package_mgr, url_program, init_lines


def _parse_cuda_info(cuda_version: str) -> Tuple[int, int]:
    """
    Turns a cuda version string into a major and minor version.

    Parameters
    ----------
    cuda_version : str
        The version string.

    Returns
    -------
    Tuple[int, int]
        The major and minor versions, in that order

    Raises
    ------
    ValueError
        If the input string does not encode a valid CUDA version number.
    """
    cuda_ver_pattern = re.compile(r"^(?P<major>[0-9]+)\." r"(?P<minor>[0-9]+)$")
    cuda_ver_match = re.match(cuda_ver_pattern, cuda_version)
    if not cuda_ver_match:
        raise ValueError(f"Malformed CUDA version: {cuda_version}")
    cuda_ver_match_groups = cuda_ver_match.groupdict()

    cuda_major: int = int(cuda_ver_match_groups["major"])
    cuda_minor: int = int(cuda_ver_match_groups["minor"])

    return (cuda_major, cuda_minor)


def _is_conda_pkg_name(line: str) -> bool:
    """
    Returns if a line appears to be an anaconda package URL

    Used for filtering lockfiles

    Parameters
    ----------
    line : str
        The line

    Returns
    -------
    bool
        True if the line appears to be an anaconda package URL, false otherwise
    """
    conda_pkg_pattern = re.compile(r"^https:\/\/conda.anaconda.org\/\S*$")
    return re.match(conda_pkg_pattern, line) is not None


def test_image(image: Image, expression: str) -> bool:
    """
    Runs a test expression on an image.

    Parameters
    ----------
    image : Image
        The image.
    expression : str
        The expression.

    Returns
    -------
    bool
        True if "test" returned with status 0, False otherwise.
    """
    try:
        image.run(f"test -d {expression}")
        return True
    except CalledProcessError as err:
        if err.returncode == 1:
            return False
        else:
            raise


class UniqueGenerator:
    """Generates random, threadsafe strings of lowercase letters and digits."""

    lock = Lock()

    @staticmethod
    def generate(k: int = 10) -> str:
        """
        Generates random, threadsafe strings of lowercase letters and digits.

        Parameters
        ----------
        k : int, optional
            The length of the string to be generated. Defaults to 10.

        Returns
        -------
        str
            The random string.
        """
        with UniqueGenerator.lock:
            return "".join(random.choices(ascii_lowercase + digits, k=k))
