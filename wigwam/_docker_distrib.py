from __future__ import annotations

import os
from textwrap import dedent

from .defaults import install_prefix


def distrib_dockerfile(
    base: str,
    source_tag: str,
    source_path: os.PathLike[str] | str,
    distrib_path: os.PathLike[str] | str,
    libdir: str,
) -> str:
    """
    Returns a Dockerfile for a distributable build.

    Parameters
    ----------
    base : str
        The base image tag.
    source_tag : str
        The tag of the image on which the project is installed.
    source_path : os.PathLike[str] or str
        The installation path of the project on the source image.
    distrib_path : os.PathLike[str] or str
        The desired installation path on the distributable image.
    libdir : str
        The base name of the directory where object libraries are stored (e.g. "lib" or
        "lib64"). This should match the value of `LIBDIR` in CMake's `GNUInstallDirs`
        module.
        See https://cmake.org/cmake/help/latest/module/GNUInstallDirs.html.

    Returns
    -------
    dockerfile: str
        The generated Dockerfile.
    """
    dockerfile: str = dedent(
        f"""
            FROM {source_tag} as source

            FROM {base}

            USER root

            COPY --from=source {source_path} {distrib_path}

            ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:{install_prefix()}/{libdir}
            ENV PYTHONPATH $PYTHONPATH:{install_prefix()}/packages

            USER $DEFAULT_USER
            ENV ISCE3_PREFIX={distrib_path}
            WORKDIR $ISCE3_PREFIX
        """
    ).strip()

    return dockerfile
