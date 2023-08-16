from __future__ import annotations

import os
from textwrap import dedent


def insert_dir_dockerfile(
    base: str,
    target_dir: str | os.PathLike[str],
    source_dir: str | os.PathLike[str] = ".",
) -> str:
    """
    Returns a Dockerfile-formatted string which inserts a given directory on the
    host machine into the image.

    This Dockerfile also places the workdir into the inserted file.

    Parameters
    ----------
    base : str
        The base image tag.
    target_dir : str | os.PathLike[str]
        The position on the image to copy to.
    source_dir : str | os.PathLike[str]
        The local directory to be copied onto the image, relative to the build context.
         Defaults to "."

    Returns
    -------
    dockerfile : str
        The generated Dockerfile.
    """
    # Arguments to the COPY command are devolved into this variable in order to keep the
    # code lines brief.
    copy_args = "--chown=$DEFAULT_GID:$DEFAULT_UID --chmod=755"

    return dedent(
        f"""
            FROM {base}

            COPY {copy_args} {source_dir} {target_dir}

            WORKDIR {target_dir}
            USER $DEFAULT_USER
        """
    ).strip()
