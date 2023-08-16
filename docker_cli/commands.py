from __future__ import annotations

import os
from shlex import split
from subprocess import DEVNULL, PIPE, run
from typing import Iterable, List

from ._docker_git import git_extract_dockerfile
from ._docker_insert import insert_dir_dockerfile
from ._docker_mamba import mamba_lockfile_command
from ._image import Image
from ._url_reader import URLReader
from ._utils import (
    image_command_check,
    is_conda_pkg_name,
    temp_image,
    universal_tag_prefix,
)


def get_archive(
    tag: str,
    base: str,
    archive_url: str,
    directory: os.PathLike[str],
    url_reader: URLReader | None = None,
):
    """
    Builds a docker image containing the requested Git archive.

    .. note:
        With this image, the workdir is moved to `directory`.

    Parameters
    ----------
    tag : str
        The image tag.
    base : str
        The base image tag.
    archive_url : str
        The URL of the Git archive to add to the image. Must be a `tar.gz` file.
    directory : path-like
        The path to the folder that the archive will be held at within the image.
    url_reader : URLReader | None, optional
        If given, will use the given URL reader to acquire the Git archive. If None,
        will check the base image and use whichever one it can find. Defaults to None.

    Returns
    -------
    Image
        The generated image.
    """
    if url_reader is None:
        with temp_image(base) as temp_img:
            _, url_reader, _ = image_command_check(temp_img)

    prefix = universal_tag_prefix()
    img_tag = tag if tag.startswith(prefix) else f"{prefix}-{tag}"

    dockerfile = git_extract_dockerfile(
        base=base,
        directory=directory,
        archive_url=archive_url,
        url_reader=url_reader,
    )

    return Image.build(tag=img_tag, dockerfile_string=dockerfile, no_cache=True)


def insert(tag: str, base: str, directory: str | os.PathLike[str]):
    """
    Builds a Docker image with the contents of the given directory copied onto it.

    The directory path on the image has the same name as the topmost directory
    of the given path. e.g. giving path "/tmp/dir/subdir" will result in the contents of
    this path being saved in "/subdir" on the generated image.

    This Dockerfile also places the working directory of the image inside of the copied
    directory.

    Parameters
    ----------
    tag : str
        The image tag.
    base : str
        The base image tag.
    directory : path-like
        The directory to be copied.

    Returns
    -------
    Image
        The generated image.
    """

    prefix = universal_tag_prefix()
    img_tag = tag if tag.startswith(prefix) else f"{prefix}-{tag}"

    dir_str = str(directory)

    # The absolute path of the given directory will be the build context.
    # This is necessary because otherwise docker may be unable to find the directory if
    # the build context is at the current working directory.
    path_absolute = os.path.abspath(str(dir_str))
    # Additionally, the top directory of the given path will be the name of the
    # directory in the image.
    if os.path.isdir(dir_str):
        target_dir = os.path.basename(path_absolute)
    else:
        target_dir = os.path.basename(os.path.dirname(path_absolute))

    # Generate the dockerfile.
    dockerfile: str = insert_dir_dockerfile(
        base=base,
        target_dir=target_dir,
        source_dir=".",
    )

    # Build the image with the context at the absolute path of the given path.
    return Image.build(
        tag=img_tag, context=path_absolute, dockerfile_string=dockerfile, no_cache=True
    )


def dropin(tag: str) -> None:
    """
    Initiates a drop-in session on an image.

    Parameters
    ----------
    tag : str
        The tag or ID of the image.
    """
    image: Image = Image(tag)

    image.drop_in()


def remove(
    tags: Iterable[str],
    force: bool = False,
    verbose: bool = False,
    ignore_prefix: bool = False,
) -> None:
    """
    Remove all Docker images that match a given tag or wildcard pattern.

    This tag or wildcard will take the form [UNIVERSAL PREFIX]-[tag or wildcard] if the
    prefix does not already match this.

    Parameters
    ----------
    tags : Iterable[str]
        An iterable of tags or wildcards to be removed.
    force : bool, optional
        Whether or not to force the removal. Defaults to False.
    verbose : bool, optional
        Whether or not to print output for removals verbosely. Defaults to False.
    ignore_prefix: bool, optional
        Whether or not to ignore the universal prefix and only use the tag or wildcard.
        Use with caution, as this will remove ALL images matching the wildcard.
        e.g. ``remove(["*"], ignore_prefix = True)`` will remove all images.
    """
    force_arg = "--force " if force else ""

    # The None below corresponds to printing outputs to the console. DEVNULL causes the
    # outputs to be discarded.
    output = None if verbose else DEVNULL

    # Search for and delete all images matching each tag or wildcard.
    for tag in tags:
        prefix = universal_tag_prefix()
        search = tag if (tag.startswith(prefix) or ignore_prefix) else f"{prefix}-{tag}"
        if verbose:
            print(f"Attempting removal for tag: {search}")

        # Search for all images whose name matches this tag, acquire a list
        search_command = split(f'docker images --filter=reference="{search}" -q')
        search_result = run(search_command, text=True, stdout=PIPE, stderr=output)
        # An empty return indicates that no such images were found. Skip to the next.
        if search_result.stdout == "":
            if verbose:
                print(f"No images found matching pattern {search}. Proceeding.")
            continue
        # The names come in a list delimited by newlines. Reform this to be delimited
        # by spaces to use with `Docker rmi`.
        search_result_str = search_result.stdout.replace("\n", " ")

        # Remove all images in the list
        command = split(f"docker rmi {force_arg}{search_result_str}")
        run(command, stdout=output, stderr=output)
    if verbose:
        print("Docker removal process completed.")


def make_lockfile(
    tag: str, file: os.PathLike[str] | str, env_name: str = "base"
) -> None:
    """
    Makes a lockfile from an image.

    ..warning:
        This function only works for images that have an environment set up.

    Parameters
    ----------
    tag : str
        The tag of the image.
    file : os.PathLike[str] | str
        The file to be output to.
    env_name: str
        The name of the environment. Defaults to "base".
    """
    cmd: str = mamba_lockfile_command(env_name=env_name)
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
    lockfile_list = lockfile_other_lines + lockfile_conda_packages
    lockfile = "\n".join(lockfile_list) + "\n"

    with open(file, mode="w") as f:
        f.write(lockfile)
