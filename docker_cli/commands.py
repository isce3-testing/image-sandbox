from __future__ import annotations

import os
import re
from shlex import split
from subprocess import DEVNULL, PIPE, run
from typing import Iterable, List

from ._docker_git import git_clone_dockerfile
from ._docker_mamba import mamba_lockfile_command
from ._image import Image
from ._utils import is_conda_pkg_name, universal_tag_prefix


def clone(tag: str, base: str, repo: str, branch: str = ""):
    """
    Builds a docker image containing the requested Git repository.

    .. note:
        With this image, the workdir is moved to the github repo's root directory.

    Parameters
    ----------
    tag : str
        The image tag.
    base : str
        The base image tag.
    repo : str
        The name of the Git repo (in [USER]/[REPO_NAME] format)
    branch : str
        The branch of the Git repo. Defaults to "".

    Returns
    -------
    Image
        The generated image.
    """

    # Check that the repo pattern matches the given repo string.
    github_repo_pattern = re.compile(
        pattern=r"^(?P<user>[a-zA-Z0-9-]+)\/(?P<repo>[a-zA-Z0-9-]+)$", flags=re.I
    )
    github_repo_match = re.match(github_repo_pattern, repo)
    if not github_repo_match:
        raise ValueError(
            f"Malformed GitHub repo name: {repo} - "
            "Please use form [USER]/[REPO_NAME]."
        )
    match_dict = github_repo_match.groupdict()
    repo_name = match_dict["repo"]

    prefix = universal_tag_prefix()
    img_tag = tag if tag.startswith(prefix) else f"{prefix}-{tag}"

    header, body = git_clone_dockerfile(
        git_repo=repo, repo_branch=branch, folder_name=repo_name
    )

    dockerfile = f"{header}\n\nFROM {base}\n\n{body}"

    return Image.build(tag=img_tag, dockerfile_string=dockerfile, no_cache=True)


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
        The tag of the image
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
