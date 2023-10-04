import re
from pathlib import Path
from subprocess import PIPE
from typing import Dict, Iterator, Tuple

from pytest import fixture, mark

from wigwam import Image, mamba_install_dockerfile
from wigwam._docker_cmake import cmake_build_dockerfile, cmake_config_dockerfile

from .utils import (
    determine_scope,
    generate_tag,
    remove_docker_image,
    rough_dockerfile_validity_check,
)


@fixture(scope=determine_scope)
def mamba_cmake_dockerfile() -> Tuple[str, str]:
    """
    Returns a CMake Dockerfile for mamba.

    Returns
    -------
    header : str
        The Dockerfile header.
    body : str
        The Dockerfile body.
    """
    header, body = mamba_install_dockerfile(
        env_reqs_file=Path("test-cmake-lock-file.txt")
    )
    body = "RUN touch CMakeLists.txt\n\n" + body
    return header, body


@fixture(scope=determine_scope)
def mamba_cmake_tag() -> Iterator[str]:
    """Returns a mamba CMake image tag."""
    yield generate_tag("mamba-cmake")


@fixture(scope=determine_scope)
def mamba_cmake_image(
    mamba_cmake_dockerfile: Tuple[str, str],
    init_tag: str,
    mamba_cmake_tag: str,
    init_image: Image,  # type: ignore
) -> Iterator[Image]:
    """
    Yields a Mamba CMake image.

    Parameters
    ----------
    mamba_cmake_dockerfile : str
        The mamba CMake Dockerfile.
    init_tag : str
        The initialization image tag.
    mamba_cmake_tag : str
        The mamba CMake image tag.
    init_image : Image
        Unused; ensures the initialization image has been built.

    Yields
    ------
    Iterator[Image]
        The mamba CMake image generator.
    """
    header, body = mamba_cmake_dockerfile

    dockerfile = f"{header}\n\nFROM {init_tag}\n\n{body}"
    img = Image.build(tag=mamba_cmake_tag, dockerfile_string=dockerfile)
    yield img
    remove_docker_image(mamba_cmake_tag)


@fixture(scope=determine_scope, params=[True, False])
def with_cuda(request) -> bool:
    """A boolean governing whether or not to install with CUDA."""
    return request.param


@fixture(
    scope=determine_scope,
    params=["Release", "Debug", "RelWithDebugInfo", "MinSizeRel"],
)
def cmake_build_type(request) -> str:
    """A boolean determining the build type for a CMake configuration."""
    return request.param


@fixture(scope=determine_scope)
def cmake_config_tag() -> Iterator[str]:
    """Returns a CMake config image tag."""
    yield generate_tag("cmake-config")


@fixture(scope=determine_scope)
def example_cmake_config_dockerfile(
    mamba_cmake_tag: str,
    with_cuda: bool,
    cmake_build_type: str,
) -> str:
    """
    A dockerfile for building the CMake config image.

    Parameters
    ----------
    mamba_cmake_tag : str
        The tag of the Mamba image with CMake installed.
    with_cuda : bool
        True if using CUDA, else False.
    cmake_build_type : str
        The CMake build type. See
        `here <https://cmake.org/cmake/help/latest/variable/CMAKE_BUILD_TYPE.html>`_
        for possible values.

    Returns
    ------
    str
        The Dockerfile.
    """
    return cmake_config_dockerfile(
        base=mamba_cmake_tag,
        build_type=cmake_build_type,
        with_cuda=with_cuda,
    )


@fixture(scope=determine_scope)
def cmake_config_image(
    example_cmake_config_dockerfile: str,
    cmake_config_tag: str,
    mamba_cmake_image: Image,  # type: ignore
) -> Iterator[Image]:
    """
    Builds a CMake config image.

    Parameters
    ----------
    example_cmake_config_dockerfile : str
        A Dockerfile for building a CMake config image.
    cmake_config_tag : str
        A tag for the CMake config image.
    mamba_cmake_image : Image
        An image with CMake installed using Mamba. Unused; ensures that this image is
        built so the CMake config image can build off of it.

    Yields
    ------
    Iterator[Image]
        The CMake config image.
    """
    img = Image.build(
        tag=cmake_config_tag, dockerfile_string=example_cmake_config_dockerfile
    )
    yield img
    remove_docker_image(cmake_config_tag)


def parse_cmake_cache(cache_str: str) -> Dict[str, str]:
    """
    Parses the key-value pairs in a CMake cache into a dictionary of strings to strings.

    Parameters
    ----------
    cache_str : str
        The cache file, rendered into a string.

    Returns
    -------
    Dict[str, str]
        All cache arguments and their values.
    """
    # Remove the two types of comments that show up in the CMake cache file:
    # Lines that begin with "//" and lines that begin with "#".
    parsed_cache = re.sub(r"^//.*\n?", "", cache_str, flags=re.MULTILINE)
    parsed_cache = re.sub(r"^#.*\n?", "", parsed_cache, flags=re.MULTILINE)
    # Make a list of all non-empty lines.
    parsed_cache_list = [line for line in parsed_cache.split("\n") if line]

    # Populate a dictionary with key-value pairs of all the arguments populated in
    # The cache.
    parsed_cache_dict = {}

    # In the cache, these pairs are listed as "ARGUMENT:TYPE=VALUE"
    # We want "ARGUMENT" and "VALUE"
    for line in parsed_cache_list:
        # First, split off the value. This creates a 2-item list of
        # "ARGUMENT:TYPE" and "VALUE".
        # Do so by splitting off everything prior to the first instance of "=".
        pair = line.split("=", maxsplit=1)
        assert len(pair) == 2
        key, value = pair
        # Now, get the "ARGUMENT" part of the argument line. The rest is not used.
        if ":" in key:
            key = key.split(":")[0]
        # Place this key-value pair in the dictionary.
        parsed_cache_dict[key] = value.strip()

    # Return the dictionary.
    return parsed_cache_dict


@mark.cmake
class TestCMakeGenerators:
    """Test the CMake build process Dockerfile generators"""

    @mark.dockerfiles
    def test_cmake_config_dockerfile(
        self,
        example_cmake_config_dockerfile,
    ):
        """Tests the CMake config dockerfiles generated by the system."""
        rough_dockerfile_validity_check(example_cmake_config_dockerfile)

    @mark.dockerfiles
    def test_cmake_build_dockerfile(
        self,
    ):
        """Tests the CMake build dockerfiles generated by the system."""
        dockerfile = cmake_build_dockerfile(base="abc")
        rough_dockerfile_validity_check(dockerfile=dockerfile)

    @mark.images
    class TestCMakeImages:
        def test_cmake_config_build(
            self,
            cmake_config_image: Image,
            with_cuda: bool,
            cmake_build_type: str,
        ):
            """Tests that the CMake config build correctly functions."""
            # Confirm that the cache exists by attempting to run `cat` on it. Capture
            # the output of this command.
            cache = cmake_config_image.run(
                "cat $BUILD_PREFIX/CMakeCache.txt", stdout=PIPE
            )

            # Parse the cache into a dictionary.
            cache_dict = parse_cmake_cache(cache_str=cache)
            # Check that the `WITH_CUDA` argument stored in the cache is consistent with
            # the with_cuda argument that this image was built with.
            cached_with_cuda = cache_dict["WITH_CUDA"]
            if with_cuda:
                assert cached_with_cuda == "YES"
            else:
                assert cached_with_cuda == "NO"

            # Check that the build type in the cache is equal to the one that this image
            # was built with.
            cached_build_type = cache_dict["CMAKE_BUILD_TYPE"]
            assert cached_build_type == cmake_build_type

        @mark.isce3
        @mark.slow
        def test_cmake_build_image(
            self,
            isce3_cmake_build_image: Image,
        ):
            """
            Test the CMake build image.

            NOTE: This test runs very slowly because it requires the building of all
            ISCE3 base images.
            """
            isce3_cmake_build_image.run(command="test cxx/isce3/libisce3.so")
