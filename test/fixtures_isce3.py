"""This file contains fixtures that are needed for building ISCE3."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterator, Tuple

from pytest import fixture

from wigwam import Image, URLReader
from wigwam._docker_cmake import (
    cmake_build_dockerfile,
    cmake_config_dockerfile,
    cmake_install_dockerfile,
)
from wigwam._docker_distrib import distrib_dockerfile
from wigwam._docker_git import git_extract_dockerfile
from wigwam._utils import get_libdir
from wigwam.defaults import install_prefix
from wigwam.setup_commands import setup_all

from .utils import determine_scope, generate_tag, remove_docker_image


@fixture(scope=determine_scope)
def env_files_dir_path() -> Path:
    """Return the path to the ISCE3 environment files directory."""
    return Path(__file__).parent.parent / "env_files"


@fixture(scope=determine_scope)
def runtime_lockfile_path(env_files_dir_path: Path) -> Path:
    """Return the path to the ISCE3 runtime lock file."""
    return env_files_dir_path / "lock-runtime.txt"


@fixture(scope=determine_scope)
def dev_lockfile_path(env_files_dir_path: Path) -> Path:
    """Return the path to the ISCE3 dev lock file."""
    return env_files_dir_path / "lock-dev.txt"


@fixture(scope=determine_scope)
def isce3_build_tag() -> str:
    """Return a tag for images in the ISCE3 build chain."""
    return generate_tag("isce3-setup")


@fixture(scope=determine_scope)
def isce3_setup_images(
    isce3_build_tag: str,
    base_tag: str,
    cuda_version: Tuple[int, int],
    cuda_repo_ver: str,
    runtime_lockfile_path: Path,
    dev_lockfile_path: Path,
) -> Iterator[dict[str, Image]]:
    """Return a dictionary of ISCE3 setup images."""
    cuda_major, cuda_minor = cuda_version

    image_dict = setup_all(
        base=base_tag,
        tag=isce3_build_tag,
        no_cache=False,
        cuda_version=f"{cuda_major}.{cuda_minor}",
        cuda_repo=cuda_repo_ver,
        runtime_env_file=runtime_lockfile_path,
        dev_env_file=dev_lockfile_path,
        verbose=True,
        test=True,
    )

    yield image_dict

    for tag in image_dict:
        remove_docker_image(tag)


@fixture(scope=determine_scope)
def isce3_env_dev_image_tag(
    isce3_build_tag: str,
    isce3_setup_images: dict[str, Image],
) -> str:
    """Return the tag of the ISCE3 development environment image."""
    pattern = re.compile(rf".*{isce3_build_tag}.*mamba-dev")
    for tag in isce3_setup_images:
        if pattern.match(tag):
            return tag

    raise ValueError("No development environment image tag found.")


@fixture(scope=determine_scope)
def isce3_env_runtime_image_tag(
    isce3_build_tag: str,
    isce3_setup_images: dict[str, Image],
) -> str:
    """Return the tag of the ISCE3 development environment image."""
    pattern = re.compile(rf".*{isce3_build_tag}.*mamba-runtime")
    for tag in isce3_setup_images:
        if pattern.match(tag):
            return tag

    raise ValueError("No development environment image tag found.")


@fixture(scope=determine_scope)
def isce3_git_repo_tag() -> str:
    """Return a tag for the ISCE3 repository image."""
    return generate_tag("isce3-repo")


@fixture(scope=determine_scope)
def isce3_git_repo_image(
    isce3_env_dev_image_tag: str,
    isce3_git_repo_tag: str,
    base_properties: Tuple[Any, URLReader],
) -> Iterator[Image]:
    """Return a tag for the ISCE3 repository image."""
    archive = "https://github.com/isce-framework/isce3/archive/refs/tags/v0.16.0.tar.gz"
    _, url_reader = base_properties

    dockerfile = git_extract_dockerfile(
        base=isce3_env_dev_image_tag,
        archive_url=archive,
        directory=Path("/src/"),
        url_reader=url_reader,
    )

    yield Image.build(
        tag=isce3_git_repo_tag, dockerfile_string=dockerfile, no_cache=False
    )

    remove_docker_image(isce3_git_repo_tag)


@fixture(scope=determine_scope)
def isce3_cmake_config_tag() -> str:
    """Return a tag for the ISCE3 CMake config image."""
    return generate_tag("isce3-cmake-config")


@fixture(scope=determine_scope)
def isce3_cmake_config_image(
    isce3_cmake_config_tag: str,
    isce3_git_repo_tag: str,
    isce3_git_repo_image: Image,  # type: ignore
) -> Iterator[Image]:
    """Return the ISCE3 CMake config image."""

    dockerfile = cmake_config_dockerfile(
        base=isce3_git_repo_tag,
        build_type="Release",
        with_cuda=True,
    )

    yield Image.build(
        tag=isce3_cmake_config_tag, dockerfile_string=dockerfile, no_cache=False
    )

    remove_docker_image(isce3_cmake_config_tag)


@fixture(scope=determine_scope)
def isce3_cmake_build_tag() -> str:
    """Return a tag for the ISCE3 CMake build image."""
    return generate_tag("isce3-cmake-build")


@fixture(scope=determine_scope)
def isce3_cmake_build_image(
    isce3_cmake_build_tag: str,
    isce3_cmake_config_tag: str,
    isce3_cmake_config_image: Image,  # type: ignore
) -> Iterator[Image]:
    """Return the ISCE3 CMake build image."""

    dockerfile = cmake_build_dockerfile(
        base=isce3_cmake_config_tag,
    )

    yield Image.build(
        tag=isce3_cmake_build_tag, dockerfile_string=dockerfile, no_cache=False
    )

    remove_docker_image(isce3_cmake_build_tag)


@fixture(scope=determine_scope)
def isce3_cmake_install_tag() -> str:
    """Return a tag for the ISCE3 CMake install image."""
    return generate_tag("isce3-cmake-install")


@fixture(scope=determine_scope)
def isce3_cmake_install_image(
    isce3_cmake_install_tag: str,
    isce3_cmake_build_tag: str,
    isce3_cmake_build_image: Image,  # type: ignore
) -> Iterator[Image]:
    """Return the ISCE3 CMake install image."""
    dockerfile = cmake_install_dockerfile(base=isce3_cmake_build_tag)

    yield Image.build(
        tag=isce3_cmake_install_tag,
        dockerfile_string=dockerfile,
        no_cache=False,
    )

    remove_docker_image(isce3_cmake_install_tag)


@fixture(scope=determine_scope)
def isce3_distributable_tag() -> str:
    """Return a tag for the ISCE3 CMake install image."""
    return generate_tag("isce3-distributable")


@fixture(scope=determine_scope)
def isce3_distributable_image(
    isce3_distributable_tag: str,
    isce3_cmake_install_tag: str,
    isce3_env_runtime_image_tag: str,
    isce3_cmake_install_image: Image,  # type: ignore
) -> Iterator[Image]:
    """Return the ISCE3 distributable image."""
    libdir = get_libdir(isce3_cmake_install_tag)

    dockerfile = distrib_dockerfile(
        base=isce3_env_runtime_image_tag,
        source_tag=isce3_cmake_install_tag,
        source_path=install_prefix(),
        distrib_path=install_prefix(),
        libdir=libdir,
    )

    yield Image.build(
        tag=isce3_distributable_tag,
        dockerfile_string=dockerfile,
        no_cache=False,
    )

    remove_docker_image(isce3_distributable_tag)
