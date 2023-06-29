import os
from shlex import split
from subprocess import DEVNULL, PIPE, CalledProcessError, run
from typing import Iterable, List, Union

from ._docker_mamba import mamba_lockfile_command
from ._exceptions import ImageNotFoundError
from ._image import Image
from ._utils import is_conda_pkg_name, universal_tag_prefix


def dropin(tag: str) -> None:
    """
    Initiates a drop-in session on an image.

    Parameters
    ----------
    tag : str
        The tag or ID of the image.
    """
    try:
        image: Image = Image(tag)
    except ImageNotFoundError as err:
        print(f"Error: {str(err)}")
        exit(1)

    image.drop_in()
    print("Drop-in session ended.")
    exit()


def remove(
    tags: Iterable[str],
    force: bool = True,
    quiet: bool = False,
    ignore_prefix: bool = False,
) -> None:
    """
    Remove all Docker images that fit a given tag or wildcard.

    This tag or wildcard will take the form [UNIVERSAL PREFIX]-[tag or wildcard] if the
    prefix does not already fit this.

    Parameters
    ----------
    force : bool, optional
        Whether or not to force the removal. Defaults to True.
    tags : Iterable[str]
        An iterable of tags or wildcards to be removed.
    quiet : bool, optional
        Whether or not to run quietly. Defaults to False.
    ignore_prefix: bool, optional
        Whether or not to ignore the universal prefix and only use the tag or wildcard.
        Use with caution, as this will remove ALL images matching the wildcard.
        e.g. remove(["*"], ignore_prefix = True) will remove all images.
    """
    force_arg = "--force " if force else ""
    output = DEVNULL if quiet else None

    # Search for and delete all images fitting each tag or wildcard.
    for tag in tags:
        prefix = universal_tag_prefix()
        search = tag if (tag.startswith(prefix) or ignore_prefix) else f"{prefix}-{tag}"
        if not quiet:
            print(f"Attempting removal for tag: {search}")

        # Search for all images whose name fits this tag, acquire a list
        search_command = split(f'docker images --filter=reference="{search}" -q')
        try:
            search_result = run(search_command, text=True, stdout=PIPE, stderr=output)
        # A CalledProcessError here indicates that the search failed. Skip to the next.
        except CalledProcessError as err:
            if not quiet:
                print(
                    f"Search for {search} failed with error code {err.returncode}. "
                    "Proceeding."
                )
            continue
        # An empty return indicates that no such images were found. Skip to the next.
        if search_result.stdout == "":
            if not quiet:
                print(f"No images found fitting pattern {search}. Proceeding.")
            continue
        # The names come in a list delimited by newlines. Reform this to be delimited
        # by spaces to use with `Docker rmi`.
        search_result_str = " ".join(search_result.stdout.split("\n"))

        # Remove all images in the list
        command = split(f"docker rmi {force_arg}{search_result_str}")
        command += []
        try:
            run(command, stdout=output, stderr=output)
        except CalledProcessError as err:
            if not quiet:
                print(
                    f"Removal of {tag} failed with error code {err.returncode}. "
                    "Proceeding."
                )
    if not quiet:
        print("Docker removal process completed.")


def make_lockfile(
    tag: str, file: Union[str, os.PathLike[str]], env_name: str = "base"
) -> None:
    """
    Makes a lockfile from an image.

    ..warning:
        This function only works for images that have an environment set up.

    Parameters
    ----------
    tag : str
        The tag of the image
    filename : Union[str, os.PathLike[str]]
        The file to be output to.
    env_name: str
        The name of the environment. Defaults to "base".
    """
    cmd: str = str(mamba_lockfile_command(env_name=env_name))
    image: Image = Image(tag)
    lockfile: str = image.run(command=cmd, stdout=PIPE)
    assert isinstance(lockfile, str)

    # Split the lockfile into two parts - initial lines and conda package lines.
    lockfile_list: List[str] = lockfile.split("\n")
    conda_package_filter = filter(is_conda_pkg_name, lockfile_list)
    other_lines_filter = filter(
        lambda line: not is_conda_pkg_name(line) and line != "", lockfile_list
    )
    lockfile_conda_packages: List[str] = list(conda_package_filter)
    lockfile_other_lines: List[str] = list(other_lines_filter)

    # Sort the conda packages, then join the parts back together.
    lockfile_conda_packages.sort()
    lockfile_list = lockfile_other_lines
    lockfile_list.extend(lockfile_conda_packages)
    lockfile = "\n".join(lockfile_list) + "\n"
    # print (lockfile)

    with open(file, mode="w") as f:
        f.write(lockfile)
