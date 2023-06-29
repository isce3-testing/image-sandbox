from __future__ import annotations

import os
import textwrap
from typing import Iterable, List, Optional, Tuple, overload


def mamba_install_dockerfile(
    env_specfile: os.PathLike[str] | str = "spec-file.txt",
) -> Tuple[str, str]:
    """
    Creates and returns a dockerfile for installing micromamba.

    Parameters
    ----------
    env_specfile : os.PathLike, optional
        The path to the specfile, by default "spec-file.txt"

    Returns
    -------
    str
        The generated dockerfile body.
    """
    body = _mamba_install_body(env_specfile=env_specfile)
    header = _mamba_install_prefix()
    return header, body


def mamba_add_specs_dockerfile(
    env_specfile: os.PathLike[str] | str = "spec-file.txt",
) -> str:
    """
    Creates a dockerfile for adding micromamba environment specs.

    Parameters
    ----------
    env_specfile : os.PathLike, optional
        The path to the specfile, by default "spec-file.txt"

    Returns
    -------
    str
        The generated dockerfile body.
    """
    return _mamba_spec_command(
        specfile=env_specfile, command="install", channels=["conda-forge"]
    )


def mamba_add_packages_dockerfile(
    packages: Iterable[str], channels: Optional[Iterable[str]]
) -> str:
    """
    Creates a dockerfile body for adding the given packages to a micromamba environment.

    Parameters
    ----------
    packages : Iterable[str]
        The set of packages to be added to the environment.
    channels: Iterable[str], optional
        Channels to look for packages in.

    Returns
    -------
    str
        The dockerfile body.
    """
    return _mamba_spec_command(packages=packages, channels=channels, command="install")


def mamba_lockfile_command(
    env_name: str,
) -> str:
    """
    Returns a command to generate a lockfile with micromamba.

    Parameters
    ----------
    env_name : str
        The name of the environment for which a dockerfile should be generated.

    Returns
    -------
    str
        The command.
    """
    cmd = ["micromamba", "env", "export", "--name", env_name, "--explicit", "--no-md5"]
    return str(" ".join(cmd))


def micromamba_docker_lines():
    return textwrap.dedent(
        """
        ARG MAMBA_DOCKERFILE_ACTIVATE=1

        USER $MAMBA_USER
        """
    ).strip()


@overload
def _mamba_spec_command(
    command: str,
    *,
    channels: Optional[Iterable[str]],
    packages: Iterable[str],
    env_name: Optional[str] = ...,
) -> str:
    ...


@overload
def _mamba_spec_command(
    command: str,
    *,
    channels: Optional[Iterable[str]],
    specfile: os.PathLike[str] | str,
    env_name: Optional[str] = ...,
) -> str:
    ...


def _mamba_spec_command(
    command, *, channels, specfile=None, packages=None, env_name=None
) -> str:
    if (specfile is not None) and (packages is not None):
        raise ValueError("Specfile and packages both given. Use only one.")
    if command not in ["install", "create"]:
        raise ValueError(
            "Improper value given for micromamba specs installation. "
            'Please use one of "install" or "create".'
        )

    # If a name was given for the environment, an argument will be added to all
    # micromamba installation commands.
    if env_name is None:
        name_arg: str = ""
    else:
        name_arg = f" -n {env_name}"

    # The output, with lines arranged into a list.
    command_list: List[str] = ["ARG MAMBA_DOCKERFILE_ACTIVATE=1", ""]
    if channels is not None:
        channels_arg = f" -c {' '.join(channels)} --override-channels"

    # If a specfile is given, give the instructions for copying and installing a
    # specfile.
    if specfile is not None:
        command_list += [
            f"COPY {specfile} /tmp/spec-file.txt",
            f"RUN micromamba {command}{name_arg}{channels_arg} -y -f "
            "/tmp/spec-file.txt \\",
            " && rm /tmp/spec-file.txt \\",
        ]
    # Otherwise packages were given, so give the instructions for installing the
    # packages.
    else:
        packages_str = " ".join(packages)
        install_command = f"micromamba {command}{name_arg}{channels_arg} -y"
        command_list += [
            f"RUN {install_command} {packages_str} \\ && micromamba update --all \\ "
        ]

    command_list += [" && micromamba clean --all --yes"]
    # Assemble this command into a portion of a dockerfile string.
    cmd: str = "\n".join(command_list)

    return cmd


def _mamba_install_prefix():
    return "FROM mambaorg/micromamba:1.3.1 as micromamba"


def _mamba_install_body(env_specfile: os.PathLike[str] | str = "spec-file.txt"):
    # String variables to keep some of the COPY lines short
    bin = "/usr/local/bin/"
    activate_current_env = f"{bin}_activate_current_env.sh"
    dockerfile_shell = f"{bin}_dockerfile_shell.sh"
    entrypoint = f"{bin}_entrypoint.sh"
    initialize_user_account = f"{bin}_dockerfile_initialize_user_accounts.sh"
    setup_root_prefix = f"{bin}_dockerfile_setup_root_prefix.sh"

    body: str = (
        textwrap.dedent(
            f"""
        USER root

        # if your image defaults to a non-root user, then you may want to make
        # the next 3 ARG commands match the values in your image. You can get
        # the values by running: docker run --rm -it my/image id -a
        ENV MAMBA_USER=$DEFAULT_USER
        ENV MAMBA_USER_ID=$DEFAULT_UID
        ENV MAMBA_USER_GID=$DEFAULT_GID

        # ENV MAMBA_USER=$MAMBA_USER
        ENV MAMBA_ROOT_PREFIX="/opt/conda"
        ENV MAMBA_EXE="/bin/micromamba"

        COPY --from=micromamba "$MAMBA_EXE" "$MAMBA_EXE"
        COPY --from=micromamba {activate_current_env} {activate_current_env}
        COPY --from=micromamba {dockerfile_shell} {dockerfile_shell}
        COPY --from=micromamba {entrypoint} {entrypoint}
        COPY --from=micromamba {activate_current_env} {activate_current_env}
        COPY --from=micromamba {initialize_user_account} {initialize_user_account}
        COPY --from=micromamba {setup_root_prefix} {setup_root_prefix}

        RUN {initialize_user_account} \\
         && {setup_root_prefix}

        USER $MAMBA_USER

        SHELL ["{dockerfile_shell}"]

        ENTRYPOINT ["{entrypoint}"]
        # Optional: if you want to customize the ENTRYPOINT and have a conda
        # environment activated, then do this:
        # ENTRYPOINT ["{entrypoint}", "my_entrypoint_program"]

    """
        ).strip()
        + "\n"
    )
    body += _mamba_spec_command(
        specfile=str(env_specfile), command="install", channels=["conda-forge"]
    )

    return body
