import os
import textwrap
from typing import List, Optional, Union

from ._dockerfile import Dockerfile


def mamba_install_dockerfile(
    env_specfile: Union[os.PathLike[str], str] = "spec-file.txt"
) -> Dockerfile:
    """
    Creates and returns a Dockerfile for installing micromamba.

    Parameters
    ----------
    env_specfile : os.PathLike, optional
        The path to the specfile, by default "spec-file.txt"

    Returns
    -------
    Dockerfile
        The generated dockerfile.
    """
    body = _mamba_install_body(
        env_specfile=env_specfile
    )
    return Dockerfile(
        header=_mamba_install_prefix(),
        body=body
    )


def mamba_add_specs_dockerfile(
    env_specfile: Union[os.PathLike, str] = "spec-file.txt"
) -> Dockerfile:
    """
    Creates a Dockerfile for adding micromamba environment specs.

    Parameters
    ----------
    env_specfile : os.PathLike, optional
        The path to the specfile, by default "spec-file.txt"

    Returns
    -------
    Dockerfile
        The generated dockerfile.
    """
    body = _mamba_spec_command(
        specfile=env_specfile,
        command="install"
    )
    return Dockerfile(body=body)


def mamba_lockfile_command(
    env_name: str,
    *,
    stringify: bool = False
) -> Union[str, List[str]]:
    """
    Returns a command to generate a lockfile with micromamba.

    Parameters
    ----------
    env_name : str
        The name of the environment for which a dockerfile should be generated.
    stringify : bool, optional
        Whether to return a string or list - if true, will return a string.
            Defaults to False.

    Returns
    -------
    Union[str, List[str]]
        The command.
    """
    cmd = ["micromamba", "env", "export", "--name", env_name, "--explicit", "--no-md5"]
    if stringify:
        return str(" ".join(cmd))
    return cmd


def micromamba_docker_lines():
    return textwrap.dedent("""
        ARG MAMBA_DOCKERFILE_ACTIVATE=1

        USER $MAMBA_USER
        """).strip()


def _mamba_spec_command(
    specfile: Union[os.PathLike[str], str],
    command: str,
    env_name: Optional[str] = None
) -> str:
    if env_name is None:
        name_arg: str = ""
    else:
        name_arg = f" -n {env_name}"
    command = textwrap.dedent(f"""
        ARG MAMBA_DOCKERFILE_ACTIVATE=1

        COPY {specfile} /tmp/spec-file.txt

        RUN micromamba {command}{name_arg} -y -f /tmp/spec-file.txt \\
         && micromamba clean --all --yes \\
         && rm /tmp/spec-file.txt
        """).strip()

    return command


def _mamba_install_prefix():
    return "FROM mambaorg/micromamba:1.3.1 as micromamba"


def _mamba_install_body(env_specfile: Union[os.PathLike[str], str] = "spec-file.txt"):
    # String variables to keep some of the COPY lines short
    bin = "/usr/local/bin/"
    activate_current_env = f"{bin}_activate_current_env.sh"
    dockerfile_shell = f"{bin}_dockerfile_shell.sh"
    entrypoint = f"{bin}_entrypoint.sh"
    initialize_usr_acct = f"{bin}_dockerfile_initialize_user_accounts.sh"
    setup_root_pfx = f"{bin}_dockerfile_setup_root_prefix.sh"

    body: str = textwrap.dedent(f'''
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
        COPY --from=micromamba {initialize_usr_acct} {initialize_usr_acct}
        COPY --from=micromamba {setup_root_pfx} {setup_root_pfx}

        RUN {initialize_usr_acct} \\
         && {setup_root_pfx}

        USER $MAMBA_USER

        SHELL ["{dockerfile_shell}"]

        ENTRYPOINT ["{entrypoint}"]
        # Optional: if you want to customize the ENTRYPOINT and have a conda
        # environment activated, then do this:
        # ENTRYPOINT ["{entrypoint}", "my_entrypoint_program"]

    ''').strip() + "\n"
    body += _mamba_spec_command(
        specfile=str(env_specfile),
        command="install"
    )

    return body
