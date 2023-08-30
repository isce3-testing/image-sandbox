from textwrap import dedent

from ._docker_mamba import micromamba_docker_lines
from .defaults import build_prefix, install_prefix


def cmake_config_dockerfile(
    base: str,
    build_type: str,
    with_cuda: bool = True,
) -> str:
    """
    Creates a dockerfile for configuring CMAKE.

    Parameters
    ----------
    base : str
        The base image tag.
    build_type : str
        The CMAKE build type.
    with_cuda : bool
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
        additional_args += ["-DWITH_CUDA=YES"]
    cmake_extra_args = " ".join(additional_args)

    # Begin constructing the dockerfile with the initial FROM line.
    dockerfile: str = f"FROM {base}\n\n"

    # Activate the micromamba user and environment.
    dockerfile += micromamba_docker_lines() + "\n\n"
    dockerfile += dedent(
        f"""
            ENV INSTALL_PREFIX {str(install_prefix())}
            ENV BUILD_PREFIX {str(build_prefix())}
            ENV PYTHONPATH $INSTALL_PREFIX/packages:$PYTHONPATH

            RUN cmake \\
                -B $BUILD_PREFIX \\
                -G Ninja \\
                -DISCE3_FETCH_DEPS=NO \\
                -DCMAKE_BUILD_TYPE={build_type} \\
                -DCMAKE_INSTALL_PREFIX=$INSTALL_PREFIX \\
                -DCMAKE_PREFIX_PATH=$MAMBA_ROOT_PREFIX \\
                -DWITH_CUDA=YES \\
                {cmake_extra_args} \\
                .
        """
    ).strip()

    return dockerfile
