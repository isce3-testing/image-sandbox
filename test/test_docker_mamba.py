from typing import Iterator

from pytest import fixture, mark

from docker_cli import Dockerfile, Image
from docker_cli._docker_mamba import (mamba_add_specs_dockerfile,
                                      mamba_install_dockerfile)

from .utils import (determine_scope, generate_tag, remove_docker_image,
                    rough_dockerfile_validity_check)


@fixture(scope=determine_scope)
def mamba_runtime_dockerfile() -> Dockerfile:
    """
    Returns a runtime dockerfile for mamba.

    Returns
    -------
    Dockerfile
        The dockerfile.
    """
    return mamba_install_dockerfile(
        env_specfile="test-runtime-lock-file.txt"
    )


@fixture(scope=determine_scope)
def mamba_runtime_tag() -> Iterator[str]:
    """
    Returns a mamba runtime image tag.

    Returns
    -------
    str
        The tag.
    """
    yield generate_tag("mamba-runtime")


@fixture(scope=determine_scope)
def mamba_runtime_image(
    mamba_runtime_dockerfile: Dockerfile,
    init_tag: str,
    mamba_runtime_tag: str,
    init_image: Image           # type: ignore
) -> Iterator[Image]:
    """
    Yields a Mamba runtime image.

    Parameters
    ----------
    mamba_runtime_dockerfile : Dockerfile
        The mamba runtime dockerfile.
    init_tag : str
        The initialization image tag.
    mamba_runtime_tag : str
        The mamba runtime tag.
    init_image : Image
        Unused; ensures the initialization image has been built.

    Yields
    ------
    Iterator[Image]
        The mamba runtime image generator.
    """
    img = mamba_runtime_dockerfile.build(
        tag=mamba_runtime_tag,
        base=init_tag
    )
    yield img
    remove_docker_image(mamba_runtime_tag)


@fixture(scope=determine_scope)
def mamba_dev_dockerfile() -> Dockerfile:
    """
    Returns a mamba dev dockerfile.

    Returns
    -------
    Dockerfile
        The dockerfile.
    """
    return mamba_add_specs_dockerfile(
        env_specfile="test-dev-lock-file.txt"
    )


@fixture(scope=determine_scope)
def mamba_dev_tag() -> Iterator[str]:
    """
    Returns an image tag for the mamba dev image.

    Returns
    -------
    str
        The tag.
    """
    yield generate_tag("mamba-dev")


@fixture(scope=determine_scope)
def mamba_dev_image(
    mamba_dev_dockerfile: Dockerfile,
    mamba_runtime_tag: str,
    mamba_dev_tag: str,
    mamba_runtime_image: Image          # type: ignore
) -> Iterator[Image]:
    """
    Returns a mamba dev image.

    Parameters
    ----------
    mamba_dev_dockerfile : Dockerfile
        The dockerfile for the image.
    mamba_runtime_tag : str
        The runtime image tag.
    mamba_dev_tag : str
        The dev image tag.
    mamba_runtime_image : Image
        Unused. Ensures the runtime image has been built.

    Yields
    ------
    Iterator[Image]
        The mamba dev image generator.
    """
    img = mamba_dev_dockerfile.build(
        tag=mamba_dev_tag,
        base=mamba_runtime_tag
    )
    yield img
    remove_docker_image(mamba_dev_tag)


@mark.mamba
class TestMambaGenerators:
    """Test the mamba environment dockerfile generators"""

    @mark.dockerfiles
    def test_mamba_install_dockerfile(self, mamba_runtime_dockerfile: Dockerfile):
        """Tests the mamba_install_dockerfile function."""
        dockerfile_string = mamba_runtime_dockerfile.full_dockerfile("%TEST_IMAGE%")

        rough_dockerfile_validity_check(dockerfile_string)

    @mark.dockerfiles
    def test_mamba_add_specs_dockerfile(self, mamba_dev_dockerfile: Dockerfile):
        """Tests the mamba_install_dockerfile function."""
        dockerfile_string = mamba_dev_dockerfile.full_dockerfile("%TEST_IMAGE%")

        rough_dockerfile_validity_check(dockerfile_string)

    @mark.images
    class TestMambaImages:
        def test_mamba_runtime_build(self, mamba_runtime_image: Image):
            """Tests that the runtime build correctly functions."""
            mamba_runtime_image.run("python")

        def test_mamba_dev_build(self, mamba_dev_image: Image):
            """Tests that the runtime build correctly functions."""
            mamba_dev_image.run("python -c \"import scipy\"")