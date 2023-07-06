from __future__ import annotations

import textwrap
from abc import ABC, abstractmethod
from typing import Iterable, List

from ._package_manager import PackageManager, get_package_manager
from ._url_reader import URLReader


class CUDADockerfileGenerator(ABC):
    """
    An abstract base class for CUDA Dockerfile generators.

    CUDA Dockerfile generators receive a CUDA version and base image, and can
    produce a Dockerfile that contains instructions for building CUDA on the
    given system.
    """

    _runtime_build_targets: List[str] = [
        "cuda-cudart-$CUDA_PKG_VERSION",
        "libcufft-$CUDA_PKG_VERSION",
    ]
    _dev_build_targets: List[str] = []

    def __init__(self, url_reader: URLReader):
        self.url_reader = url_reader

    def generate_runtime_dockerfile(
        self,
        cuda_ver_major: int,
        cuda_ver_minor: int,
        repo_ver: str,
        *,
        arch: str = "x86_64",
        nvidia_visible_devices: str = "all",
        nvidia_driver_capabilities: str = "compute,utility",
    ) -> str:
        """
        Generates a Dockerfile for the CUDA runtime image.

        Parameters
        ----------
        cuda_ver_major : int
            The major CUDA version.
        cuda_ver_minor : int
            The minor CUDA version.
        nvidia_visible_devices : str, optional
            The value to set the nvidia_visible_devices environment variable
            to, by default "all"
        nvidia_driver_capabilities : str, optional
            The value to set the nvidia_driver_capabilities environment
            variable to, by default "compute,utility"

        Returns
        -------
        str
            The generated Dockerfile body

        Raises
        ------
        ValueError
            If the major CUDA version is below 11, the minimum supported
            version.
        """

        if cuda_ver_major < 11:
            raise ValueError(  # pragma: no cover
                "CUDA version below 11 requested. Only CUDA versions >= 11 "
                "are supported."
            )
        cuda_pkg_version = '"${CUDA_VERSION_MAJOR}-${CUDA_VERSION_MINOR}"'
        nvidia_req_cuda: str = "cuda>=${CUDA_VERSION_MAJOR}.${CUDA_VERSION_MINOR}"
        body: str = self._generate_initial_lines(repo_ver, arch=arch)
        body += (
            "\n"
            + textwrap.dedent(
                f"""\
            ENV NVIDIA_VISIBLE_DEVICES {nvidia_visible_devices}
            ENV NVIDIA_DRIVER_CAPABILITIES {nvidia_driver_capabilities}
            ENV CUDA_VERSION_MAJOR {cuda_ver_major}
            ENV CUDA_VERSION_MINOR {cuda_ver_minor}
            ENV CUDA_PKG_VERSION {cuda_pkg_version}
            ENV NVIDIA_REQUIRE_CUDA {nvidia_req_cuda}
            """
            ).strip()
        )
        body += "\n" + self.generate_install_lines(
            build_targets=self._runtime_build_targets
        )
        return body

    def generate_dev_dockerfile(self) -> str:
        """
        Generates a Dockerfile for the CUDA Dev image.

        Returns
        -------
        str
            The generated Dockerfile body.
        """
        body = self.generate_install_lines(build_targets=self._dev_build_targets)

        body = "USER root\n" + body

        version_name = "${CUDA_VERSION_MAJOR}.${CUDA_VERSION_MINOR}"
        body += (
            "\n"
            + textwrap.dedent(
                f"""\
                ENV CUDAHOSTCXX=x86_64-conda-linux-gnu-c++
                ENV CUDACXX=/usr/local/cuda-{version_name}/bin/nvcc

                USER $DEFAULT_USER
                """
            ).strip()
        )
        return body

    @abstractmethod
    def _generate_initial_lines(self, repo_ver: str, *, arch: str = "x86_64") -> str:
        """
        Generates the first lines of the CUDA install Dockerfile.

        These lines typically acquire the necessary CUDA repo and configure the
        image to install CUDA.

        Returns
        -------
        str
            The initial lines of the CUDA install Dockerfile.
        """
        ...

    @abstractmethod
    def generate_install_lines(self, build_targets: Iterable[str]) -> str:
        """
        Generates the install lines for the CUDA install Dockerfile.

        These lines typically use the packet manager to install the given CUDA
        libraries and then clean the packet manager cache.

        Returns
        -------
        str
            The install lines of the CUDA install Dockerfile.
        """
        ...

    @property
    def package_manager(self) -> PackageManager:
        """
        The package manager used by this Dockerfile generator.

        This ensures that all subclasses of this class will have a package manager
        property, but doesn't require the abstract base class to specify it.

        Raises
        ------
        AttributeError
            If no package manager is present on the object.
        """
        if not hasattr(self, "_package_manager"):
            raise AttributeError(  # pragma: no cover
                "Attribute 'package_manager' not found."
            )
        return getattr(self, "_package_manager")


class AptGetCUDADockerfileGen(CUDADockerfileGenerator):
    """
    A CUDA Dockerfile generator for debian-based apt-get systems
    """

    _dev_build_targets = [
        "cuda-cudart-dev-$CUDA_PKG_VERSION",
        "cuda-nvcc-$CUDA_PKG_VERSION",
        "libcufft-dev-$CUDA_PKG_VERSION",
    ]

    def __init__(self, url_reader: URLReader):
        super(AptGetCUDADockerfileGen, self).__init__(url_reader=url_reader)
        self._package_manager: PackageManager = get_package_manager("apt-get")

    def _generate_initial_lines(self, repo_ver: str, *, arch: str = "x86_64") -> str:
        cuda_repo_name = (
            "https://developer.download.nvidia.com/"
            f"compute/cuda/repos/{repo_ver}/{arch}/"
        )
        filename = f"cuda-keyring_1.0-1_all.{self.package_manager.file_type}"
        read_section = self.url_reader.generate_read_command(
            target=f"{cuda_repo_name}" + filename,
            output_file=filename,
        )
        package_command_section = self.package_manager.generate_package_command(
            target=filename,
        )
        return f"RUN {read_section} \\\n && {package_command_section}"

    def generate_install_lines(self, build_targets: Iterable[str]) -> str:
        targets = build_targets
        install_section = self.package_manager.generate_install_command(
            targets=targets, clean=True
        )
        install_line = (
            f"RUN {self.package_manager.name} update \\\n && {install_section}"
        )
        return install_line


class YumCUDADockerfileGen(CUDADockerfileGenerator):
    """
    A CUDA Dockerfile generator for rpm-based yum systems
    """

    _dev_build_targets = [
        "cuda-cudart-devel-$CUDA_PKG_VERSION",
        "cuda-nvcc-$CUDA_PKG_VERSION",
        "libcufft-devel-$CUDA_PKG_VERSION",
        "rpm-build",
    ]

    def __init__(self, url_reader: URLReader):
        super(YumCUDADockerfileGen, self).__init__(url_reader=url_reader)
        self._package_manager: PackageManager = get_package_manager("yum")

    def _generate_initial_lines(self, repo_ver: str, *, arch: str = "x86_64") -> str:
        cuda_repo_name = (
            "https://developer.download.nvidia.com/"
            f"compute/cuda/repos/{repo_ver}/{arch}/"
        )
        cuda_repo = f"{cuda_repo_name}cuda-{repo_ver}.repo"
        return f"RUN yum-config-manager --add-repo {cuda_repo} \\\n " "&& yum clean all"

    def generate_install_lines(self, build_targets: Iterable[str]) -> str:
        targets = build_targets
        install_line = self.package_manager.generate_install_command(
            targets=targets, clean=True
        )
        install_line = "RUN " + install_line
        return install_line


def get_cuda_dockerfile_generator(
    pkg_mgr: PackageManager | str, url_reader: URLReader
) -> CUDADockerfileGenerator:
    """
    Returns the appropriate Dockerfile generator for a system.

    Parameters
    ----------
    pkg_mgr : PackageManager or str
        The package manager in use by the image
    url_reader : URLReader
        The URL reader (e.g. cURL, wget) in use by the image
    origin_image_name : str
        The name of the image on which this one is based (e.g. "ubuntu") -
        note that this is the very basis image, not the immediate parent image.
    arch : str, optional
        The architecture of the CUDA repository, by default "x86_64"

    Returns
    -------
    CUDADockerfileGenerator
        The instance of the selected CUDADockerfileGenerator

    Raises
    ------
    ValueError
        If the package manager is not associated with any
        CUDADockerfileGenerator supported by this file.
    """
    if isinstance(pkg_mgr, PackageManager):
        name = pkg_mgr.name
    elif isinstance(pkg_mgr, str):
        name = pkg_mgr
    else:
        raise ValueError("pkg_mgr argument value must be a PackageManager or str.")
    if name == "apt-get":
        return AptGetCUDADockerfileGen(url_reader=url_reader)
    elif name == "yum":
        return YumCUDADockerfileGen(url_reader=url_reader)
    else:
        raise ValueError(f"Unrecognized package manager: {name}")
