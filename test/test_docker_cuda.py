from typing import Iterator, Tuple, Type

from pytest import fixture, mark

from docker_cli import Dockerfile, Image
from docker_cli._docker_cuda import (AptGetCUDADockerfileGen,
                                     CUDADockerfileGenerator,
                                     YumCUDADockerfileGen,
                                     get_cuda_dockerfile_generator)
from docker_cli._shell_cmds import (AptGet, PackageManager, URLReader, Wget,
                                    Yum, cURL)

from .utils import (determine_scope, generate_tag, remove_docker_image,
                    rough_dockerfile_validity_check)


@mark.cuda
def test_get_cuda_dockerfile_generator():
    """Tests that the get_cuda_dockerfile_generator returns the right generator."""
    gen: CUDADockerfileGenerator = get_cuda_dockerfile_generator(AptGet(), cURL)
    assert isinstance(gen, AptGetCUDADockerfileGen)
    assert gen.url_reader == cURL

    gen = get_cuda_dockerfile_generator(Yum(), Wget)
    assert isinstance(gen, YumCUDADockerfileGen)
    assert gen.url_reader == Wget


@fixture(scope=determine_scope)
def cuda_repo_ver(base_tag: str) -> str:
    """The basic information about the cuda dockerfile or image to be generated."""
    if base_tag == "ubuntu":
        return "ubuntu2004"
    if base_tag == "oraclelinux:8.4":
        return "rhel8"
    else:
        raise ValueError(f"Unknown base tag: {base_tag}")


@fixture(scope=determine_scope)
def cuda_generator(
    base_properties: Tuple[PackageManager, Type[URLReader]]
) -> CUDADockerfileGenerator:
    """
    Returns the CUDADockerfileGenerator needed for this CUDA test.

    Parameters
    ----------
    base_properties : Tuple[PackageManager, Type[URLReader]]
        The package manager and URL reader.

    Returns
    -------
    CUDADockerfileGenerator
        The dockerfile generator.
    """
    package_mgr, url_reader = base_properties
    gen = get_cuda_dockerfile_generator(pkg_mgr=package_mgr, url_reader=url_reader)
    return gen


@fixture(scope=determine_scope)
def cuda_runtime_dockerfile(
    cuda_generator: CUDADockerfileGenerator,
    cuda_repo_ver: str
) -> Dockerfile:
    """
    Returns a runtime dockerfile for cuda.

    Returns
    -------
    Dockerfile
        The dockerfile.
    """
    dockerfile: Dockerfile = cuda_generator.generate_runtime_dockerfile(
        cuda_ver_major=11,
        cuda_ver_minor=4,
        repo_ver=cuda_repo_ver
    )
    return dockerfile


@fixture(scope=determine_scope)
def cuda_runtime_tag() -> Iterator[str]:
    """
    Returns a cuda runtime image tag.

    Returns
    -------
    str
        The tag.
    """
    yield generate_tag("cuda-runtime")


@fixture(scope=determine_scope)
def cuda_runtime_image(
    cuda_runtime_dockerfile: Dockerfile,
    init_tag: str,
    cuda_runtime_tag: str,
    init_image: Image           # type: ignore
) -> Iterator[Image]:
    """
    Yields a cuda runtime image.

    Parameters
    ----------
    cuda_runtime_dockerfile : Dockerfile
        The cuda runtime dockerfile.
    init_tag : str
        The initialization image tag.
    cuda_runtime_tag : str
        The cuda runtime tag.
    init_image : Image
        Unused; ensures the initialization image has been built.

    Yields
    ------
    Iterator[Image]
        The cuda runtime image generator.
    """
    img = cuda_runtime_dockerfile.build(
        tag=cuda_runtime_tag,
        base=init_tag
    )
    yield img
    remove_docker_image(cuda_runtime_tag)


@fixture(scope=determine_scope)
def cuda_dev_dockerfile(cuda_generator: CUDADockerfileGenerator) -> Dockerfile:
    """
    Returns a cuda dev dockerfile.

    Returns
    -------
    Dockerfile
        The dockerfile.
    """
    dockerfile = cuda_generator.generate_dev_dockerfile()
    return dockerfile


@fixture(scope=determine_scope)
def cuda_dev_tag() -> Iterator[str]:
    """
    Returns an image tag for the cuda dev image.

    Returns
    -------
    str
        The tag.
    """
    yield generate_tag("cuda-dev")


@fixture(scope=determine_scope)
def cuda_dev_image(
    cuda_dev_dockerfile: Dockerfile,
    cuda_runtime_tag: str,
    cuda_dev_tag: str,
    cuda_runtime_image: Image          # type: ignore
) -> Iterator[Image]:
    """
    Returns a cuda dev image.

    Parameters
    ----------
    cuda_dev_dockerfile : Dockerfile
        The dockerfile for the image.
    cuda_runtime_tag : str
        The runtime image tag.
    cuda_dev_tag : str
        The dev image tag.
    cuda_runtime_image : Image
        Unused. Ensures the runtime image has been built.

    Yields
    ------
    Iterator[Image]
        The cuda dev image generator.
    """
    img = cuda_dev_dockerfile.build(
        tag=cuda_dev_tag,
        base=cuda_runtime_tag
    )
    yield img
    remove_docker_image(cuda_dev_tag)


@mark.cuda
class TestCudaGen:
    """Tests the CUDADockerfileGenerator classes."""

    def test_init(
        self,
        cuda_generator: CUDADockerfileGenerator,
        base_properties: Tuple[PackageManager, Type[URLReader]]
    ):
        """Tests the constructor."""
        pkg_mgr, url_reader = base_properties
        assert isinstance(cuda_generator.package_manager, type(pkg_mgr))
        assert cuda_generator.url_reader == url_reader

    def test_generate_install_lines(
        self,
        cuda_generator: CUDADockerfileGenerator,
        base_properties: Tuple[PackageManager, Type[URLReader]]
    ):
        """Tests the generation of CUDA install lines."""
        pkg_mgr, _ = base_properties
        dummy_installs = ['a', 'b', 'c', 'd', 'e']
        install_return = cuda_generator.generate_install_lines(
            build_targets=dummy_installs)
        apt_get_install = pkg_mgr.generate_install_command(
            targets=dummy_installs,
            stringify=True
        )
        assert isinstance(apt_get_install, str)
        assert apt_get_install in install_return
        rough_dockerfile_validity_check(install_return)

    @mark.dockerfiles
    def test_generate_runtime_dockerfile(
        self,
        cuda_generator: CUDADockerfileGenerator,
        cuda_repo_ver: str
    ):
        """Tests the generation of a runtime CUDA dockerfile."""
        dockerfile: Dockerfile = cuda_generator.generate_runtime_dockerfile(
            cuda_ver_major=11,
            cuda_ver_minor=4,
            repo_ver=cuda_repo_ver
        )
        assert isinstance(dockerfile, Dockerfile)

        dockerfile_string = dockerfile.full_dockerfile("%DUMMY_BASE%")
        rough_dockerfile_validity_check(dockerfile_string)

    @mark.dockerfiles
    def test_generate_dev_dockerfile(
        self,
        cuda_generator: CUDADockerfileGenerator
    ):
        """Tests the generation of a dev CUDA dockerfile."""
        dockerfile: Dockerfile = cuda_generator.generate_dev_dockerfile()
        assert isinstance(dockerfile, Dockerfile)

        dockerfile_string = dockerfile.full_dockerfile("%DUMMY_BASE%")
        rough_dockerfile_validity_check(dockerfile_string)

    @mark.images
    class TestCUDAImages:
        def test_cuda_runtime_build(self, cuda_runtime_image: Image):
            """Tests that the runtime build correctly functions."""
            cuda_runtime_image.run("nvidia-smi")

        def test_cuda_dev_build(self, cuda_dev_image: Image):
            """Tests that the runtime build correctly functions."""
            cuda_dev_image.run("nvidia-smi")
