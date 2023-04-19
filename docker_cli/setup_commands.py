import os
from textwrap import dedent
from typing import Dict, Optional, Tuple, Type, Union

from ._dockerfile import Dockerfile
from ._image import Image
from ._shell_cmds import PackageManager, URLReader
from ._utils import (_generate_cuda_dev_dockerfile,
                     _generate_cuda_runtime_dockerfile,
                     _generate_micromamba_dev_dockerfile,
                     _generate_micromamba_runtime_dockerfile,
                     _image_command_check, _parse_cuda_info,
                     universal_tag_prefix)


def setup_init(
    base: str,
    tag: str,
    no_cache: bool
) -> Tuple[Image, PackageManager, Type[URLReader]]:
    """
    Set up the initial configuration image

    Parameters
    ----------
    base : str
        The name of the image upon this one will be based.
    tag : str
        The tag of the image to be built.
    no_cache : bool
        Run docker build with no cache if True.

    Returns
    -------
    Image
        The generated image
    PackageManager
        The package manager present on the image
    Type[URLReader]
        The URL Reader present on the image
    """
    package_mgr, url_reader, body = _image_command_check(
        base, True
    )

    dockerfile: Dockerfile = Dockerfile(body=body)

    dockerfile.append_body(dedent("""
        ENV DEFAULT_GROUP defaultgroup
        ENV DEFAULT_USER defaultuser
        ENV DEFAULT_GID 1000
        ENV DEFAULT_UID 1000

        RUN groupadd -g $DEFAULT_GID $DEFAULT_GROUP
        RUN useradd -g $DEFAULT_GID -u $DEFAULT_UID -m $DEFAULT_USER
        """).strip()
    )
    dockerfile.append_body("RUN chmod -R 777 /tmp")

    prefix = universal_tag_prefix()
    img_tag = tag if tag.startswith(prefix) else f"{prefix}-{tag}"
    image = dockerfile.build(
        tag=img_tag,
        base=base,
        no_cache=no_cache
    )

    return (image, package_mgr, url_reader)


def setup_cuda_runtime(
        base: str,
        tag: str,
        no_cache: bool,
        cuda_version: str,
        cuda_repo: str,
        package_manager: Optional[PackageManager] = None,
        url_reader: Optional[Type[URLReader]] = None
) -> Image:
    """
    Build the CUDA runtime image.

    Parameters
    ----------
    base : str
        The name of the image upon this one will be based.
    tag : str
        The tag of the image to be built.
    no_cache : bool
        Run docker build with no cache if True.
    cuda_version : str
        The CUDA version.
    cuda_repo : str
        The name of the CUDA repository for this distro.
        (e.g. 'rhel8', 'ubuntu2004')
    package_manager : PackageManager
        The package manager in use by the base image.
    url_reader : Type[URLReader]
        The URL reader in use by the base image.

    Returns
    -------
    Image
        The generated image.

    Raises
    -------
    ValueError
        If one of package_manager and url_reader is defined, but not both.
    """
    if (package_manager is not None) and (url_reader is not None):
        package_mgr = package_manager
        url_program = url_reader
        init_lines = ""
    elif (package_manager is not None) or (url_reader is not None):
        raise ValueError("Either both package_manager and url_reader must both be "
                         "defined or neither.")
    else:
        package_mgr, url_program, init_lines = _image_command_check(base)
    cuda_major, cuda_minor = _parse_cuda_info(cuda_version=cuda_version)

    dockerfile: Dockerfile = _generate_cuda_runtime_dockerfile(
        package_mgr,
        cuda_major=cuda_major,
        cuda_minor=cuda_minor,
        cuda_repo=cuda_repo,
        url_reader=url_program
    )

    dockerfile.prepend_body(init_lines)

    prefix = universal_tag_prefix()
    img_tag = tag if tag.startswith(prefix) else f"{prefix}-{tag}"
    return dockerfile.build(
        tag=img_tag,
        base=base,
        no_cache=no_cache
    )


def setup_cuda_dev(
        base: str,
        tag: str,
        no_cache: bool,
        package_manager: Optional[PackageManager] = None,
        url_reader: Optional[Type[URLReader]] = None
) -> Image:
    """
    Builds the CUDA dev image.

    Parameters
    ----------
    base : str
        The name of the image upon this one will be based.
    tag : str
        The tag of the image to be built.
    no_cache : bool
        Run docker build with no cache if True.
    package_manager : PackageManager
        The package manager in use by the base image.
    url_reader : Type[URLReader]
        The URL reader in use by the base image.

    Returns
    -------
    Image
        The generated image.

    Raises
    -------
    ValueError
        If one of package_manager and url_reader is defined, but not both.
    """
    if (package_manager is not None) and (url_reader) is not None:
        package_mgr = package_manager
        url_program = url_reader
        init_lines = ""
    elif (package_manager is not None) or (url_reader is not None):
        raise ValueError("Either both package_manager and url_reader must both be "
                         "defined or neither.")
    else:
        package_mgr, url_program, init_lines = _image_command_check(base)

    dockerfile: Dockerfile = _generate_cuda_dev_dockerfile(
        package_manager=package_mgr,
        url_reader=url_program
    )
    dockerfile.prepend_body(init_lines)

    prefix = universal_tag_prefix()
    img_tag = tag if tag.startswith(prefix) else f"{prefix}-{tag}"
    return dockerfile.build(
        tag=img_tag,
        base=base,
        no_cache=no_cache
    )


def setup_env_runtime(
        base: str,
        tag: str,
        no_cache: bool,
        env_file: Union[str, os.PathLike[str]]
) -> Image:
    """
    Builds the Conda runtime environment image with micromamba.

    Parameters
    ----------
    base : str
        The name of the image upon this one will be based.
    tag : str
        The tag of the image to be built.
    no_cache : bool
        Run docker build with no cache if True.
    env_file : str
        The location of the runtime environment spec-file.

    Returns
    -------
    Image
        The generated image.
    """

    dockerfile: Dockerfile = _generate_micromamba_runtime_dockerfile(
        env_specfile=env_file
    )

    prefix = universal_tag_prefix()
    img_tag = tag if tag.startswith(prefix) else f"{prefix}-{tag}"
    return dockerfile.build(
        tag=img_tag,
        base=base,
        no_cache=no_cache
    )


def setup_env_dev(
        base: str,
        tag: str,
        no_cache: bool,
        env_file: Union[str, os.PathLike[str]]
) -> Image:
    """
    Set up the development environment.

    Parameters
    ----------
    base : str
        The name of the image upon this one will be based.
    tag : str
        The tag of the image to be built.
    no_cache : bool
        Run docker build with no cache if True.
    env_file : str
        The location of the runtime environment spec-file.

    Returns
    -------
    Image
        The generated image.
    """

    dockerfile: Dockerfile = _generate_micromamba_dev_dockerfile(
        env_specfile=env_file
    )

    prefix = universal_tag_prefix()
    img_tag = tag if tag.startswith(prefix) else f"{prefix}-{tag}"
    return dockerfile.build(
        tag=img_tag,
        base=base,
        no_cache=no_cache
    )


def setup_all(
    base: str,
    tag: str,
    no_cache: bool,
    cuda_version: str,
    cuda_repo: str,
    runtime_env_file: os.PathLike,
    dev_env_file: os.PathLike
) -> Dict[str, Image]:
    """
    Builds the entire docker image stack.

    Parameters
    ----------
    base : str
        The name of the image upon this one will be based.
    tag : str
        The tag of the image to be built.
    no_cache : bool
        Run docker build with no cache if True.
    cuda_version : str
        The CUDA version.
    cuda_repo : str
        The name of the CUDA repository for this distro.
        (e.g. 'rhel8', 'ubuntu2004')
    runtime_env_file : os.PathLike
        The location of the runtime environment spec-file.
    dev_env_file : os.PathLike
        The location of the dev environment spec-file.

    Returns
    -------
    Dict[str, Image]
        A dictionary of all images generated, indexed by tag.
    """
    prefix = universal_tag_prefix()
    cuda_major, cuda_minor = _parse_cuda_info(cuda_version=cuda_version)

    images: Dict[str, Image] = {}

    # Build the initial image and append it to the image list
    base_image_tag = f"{prefix}-{tag}-init"
    base_image, package_mgr, url_program = setup_init(
        base=base,
        tag=base_image_tag,
        no_cache=no_cache
    )
    images[base_image_tag] = base_image

    # Build the CUDA runtime image and append it to the image list
    cuda_run_tag = f"{prefix}-{tag}-cuda-" + \
                   f"{cuda_major}-{cuda_minor}-runtime"
    cuda_run_image = setup_cuda_runtime(
        base=base_image_tag,
        tag=cuda_run_tag,
        no_cache=no_cache,
        cuda_version=cuda_version,
        cuda_repo=cuda_repo,
        package_manager=package_mgr,
        url_reader=url_program
    )
    images[cuda_run_tag] = cuda_run_image

    # Build the Mamba runtime image and append it to the image list
    mamba_run_tag = f"{prefix}-{tag}-mamba-runtime"
    mamba_run_image = setup_env_runtime(
        base=cuda_run_tag,
        tag=mamba_run_tag,
        no_cache=no_cache,
        env_file=runtime_env_file
    )
    images[mamba_run_tag] = mamba_run_image

    # Build the CUDA dev image and append it to the image list
    cuda_dev_tag = f"{prefix}-{tag}-cuda-" + \
                   f"{cuda_major}-{cuda_minor}-dev"
    cuda_dev_image = setup_cuda_dev(
        base=mamba_run_tag,
        tag=cuda_dev_tag,
        no_cache=no_cache,
        package_manager=package_mgr,
        url_reader=url_program
    )
    images[cuda_dev_tag] = cuda_dev_image

    # Build the Mamba dev image and append it to the image list
    mamba_dev_tag = f"{prefix}-{tag}-mamba-dev"
    mamba_dev_image = setup_env_dev(
        base=cuda_dev_tag,
        tag=mamba_dev_tag,
        no_cache=no_cache,
        env_file=dev_env_file
    )
    images[mamba_dev_tag] = mamba_dev_image

    return images
