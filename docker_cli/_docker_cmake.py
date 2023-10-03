from textwrap import dedent

from ._docker_mamba import micromamba_docker_lines
from .defaults import build_prefix, install_prefix


def cmake_config_dockerfile(base: str, build_type: str, with_cuda: bool = True) -> str:
    """
    Creates a Dockerfile for configuring CMake Build.

    This function assumes that the working directory on the image is at the
    source directory where the top-level CMakeLists.txt file is contained.

    Parameters
    ----------
    base : str
        The base image tag.
    build_type : str
        The CMake build type. See
        `here <https://cmake.org/cmake/help/latest/variable/CMAKE_BUILD_TYPE.html>`_
        for possible values.
    with_cuda : bool, optional
        Whether or not to use CUDA in the build. Defaults to True.

    Returns
    -------
    dockerfile : str
        The generated Dockerfile.
    """
    # Parsing the additional arguments and then joining them as a list because there may
    # be additional cmake arguments to add in the future, and this simplifies the
    # process of adding them.
    additional_args = []
    if with_cuda:
        additional_args += ["-D WITH_CUDA=YES"]
    else:
        additional_args += ["-D WITH_CUDA=NO"]
    cmake_extra_args = " ".join(additional_args)

    # Begin constructing the dockerfile with the initial FROM line.
    dockerfile: str = f"FROM {base}\n\n"

    # Activate the micromamba user and environment.
    dockerfile += micromamba_docker_lines() + "\n\n"
    dockerfile += dedent(
        f"""
            ENV INSTALL_PREFIX {str(install_prefix())}
            ENV BUILD_PREFIX {str(build_prefix())}

            RUN cmake \\
                -S . \\
                -B $BUILD_PREFIX \\
                -G Ninja \\
                -D ISCE3_FETCH_DEPS=NO \\
                -D CMAKE_BUILD_TYPE={build_type} \\
                -D CMAKE_INSTALL_PREFIX=$INSTALL_PREFIX \\
                -D CMAKE_PREFIX_PATH=$MAMBA_ROOT_PREFIX \\
                {cmake_extra_args}
        """
    ).strip()

    return dockerfile


def cmake_build_dockerfile(base: str) -> str:
    """
    Creates a dockerfile for compiling with CMake.

    Parameters
    ----------
    base : str
        The base image tag.

    Returns
    -------
    dockerfile: str
        The generated Dockerfile.
    """
    # Begin constructing the dockerfile with the initial FROM line.
    dockerfile = f"FROM {base}\n\n"

    # Run as the $MAMBA_USER and activate the micromamba environment.
    dockerfile += f"{micromamba_docker_lines()}\n\n"

    # Build the project.
    dockerfile += "RUN cmake --build $BUILD_PREFIX --parallel"

    return dockerfile