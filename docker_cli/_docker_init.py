from textwrap import dedent


def init_dockerfile(base: str, custom_lines: str) -> str:
    """
    Set up the initial configuration image.

    Parameters
    ----------
    base : str
        The name of the image upon this one will be based.
    custom_lines : str
        Custom installation and configuration lines to be added to the Dockerfile.

    Returns
    -------
    str
        The generated Dockerfile.
    """
    return (
        f"FROM {base}\n\n"
        + custom_lines
        + "\n"
        + dedent(
            """
        ENV DEFAULT_GROUP defaultgroup
        ENV DEFAULT_USER defaultuser
        ENV DEFAULT_GID 1000
        ENV DEFAULT_UID 1000

        RUN groupadd -g $DEFAULT_GID $DEFAULT_GROUP
        RUN useradd -g $DEFAULT_GID -u $DEFAULT_UID -m $DEFAULT_USER

        RUN chmod -R 777 /tmp
        """
        ).strip()
    )
