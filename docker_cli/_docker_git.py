from __future__ import annotations

import os
from pathlib import Path
from textwrap import dedent

from ._docker_mamba import micromamba_docker_lines
from ._url_reader import URLReader


def git_extract_dockerfile(
    base: str,
    archive_url: str,
    url_reader: URLReader,
    directory: str | os.PathLike[str] = Path("repo"),
) -> str:
    """
    Returns a Dockerfile-formatted string with instructions to fetch a Git archive.

    Parameters
    ----------
    base : str
        The base image for this dockerfile.
    archive_url : str
        The URL of the Git archive. Must be a `tar.gz` file.
    url_reader : URLReader
        The URL reader program to fetch the archive with.
    directory : path-like, optional
        The name of the folder to store the repository in. Defaults to "repo".

    Returns
    -------
    dockerfile : str
        The generated Dockerfile.
    """
    folder_path_str = os.fspath(directory)

    # Dockerfile preparation:
    # Prepare the repository file, ensure proper ownership and permissions.
    dockerfile = (
        dedent(
            f"""
                FROM {base}

                USER root

                RUN mkdir -p {folder_path_str}
                RUN chown -R $MAMBA_USER_ID:$MAMBA_USER_GID {folder_path_str}
                RUN chmod -R 755 {folder_path_str}
            """
        ).strip()
        + "\n"
    )

    # Switch user to 'MAMBA_USER'
    dockerfile += micromamba_docker_lines() + "\n"

    # Get the command to pull the git archive from the internet.
    fetch_command = url_reader.generate_read_command(target=archive_url)

    # Get the Git archive, extract it, move workdir to it, and change user back to
    # default.
    # The `--strip-components 1` argument to `tar` enables the archive to be unzipped
    # without appending an additional directory in addition to the `folder_path`.
    dockerfile += (
        dedent(
            f"""
        RUN {fetch_command} | tar -xvz -C {folder_path_str} --strip-components 1

        WORKDIR {directory}
        USER $DEFAULT_USER
    """
        ).strip()
        + "\n"
    )

    # Return the generated dockerfile
    return dockerfile
