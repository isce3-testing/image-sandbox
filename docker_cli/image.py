import io
import os
from shlex import split
from subprocess import PIPE, CalledProcessError, run
from sys import stdin
from typing import (Any, List, Optional, Sequence, Type, TypeVar, Union,
                    overload)

from .exceptions import CommandNotFoundOnImageError


class Image:
    """
    A docker image.

    Holds a reference to a given docker image and provides
    an interface by which to interact with that image.

    Capabilities include:
    -   Building docker images from dockerfiles or dockerfile-formatted strings
        via :func:`~docker_cli.Image.build`.
    -   Running commands in containers built from the image using
        :func:`~docker_cli.Image.run`.
    -   Inspecting properties of the given image.
    """
    Self = TypeVar("Self", bound="Image")

    def __init__(self, name_or_id: str):
        """
        Initialize a new Image object.

        Parameters
        ----------
        name_or_id : str
            A name or ID by which to find this image using docker inspect.

        Raises
        ----------
        CalledProcessError
            Via :func:`~docker_cli.get_image_id`.
        """
        self._id = get_image_id(name_or_id)

    @overload
    @classmethod
    def build(
        cls: Type[Self],
        tag: str,
        *,
        dockerfile: Optional[os.PathLike[str]],
        context: Optional[os.PathLike[str]],
        stdout: Optional[io.TextIOBase],
        stderr: Optional[io.TextIOBase],
        network: str,
        no_cache: bool
    ) -> Self:
        """
        Build a new image from a dockerfile.

        Build a Dockerfile at the given path with the given name, then
        return the associated Image instance.

        Parameters
        ----------
        tag : str
            A name for the image.
        dockerfile : os.PathLike or None, optional
            The path of the Dockerfile to build, relative to the `context`
            directory. Defaults to None.
        context : os.PathLike or None, optional
            The build context. Defaults to ".".
        stdout : io.TextIOBase or None, optional
            A file-like object that the stdout output of the docker build
            program will be redirected to. If None, no redirection will occur.
            Defaults to None.
        stderr : io.TextIOBase or None, optional
            A file-like object that the stderr output of the docker build
            program will be redirected to. If None, no redirection will occur.
            It should be noted that docker build primarily outputs to stderr.
            Defaults to None.
        network : str, optional
            The name of the network. Defaults to "host".
        no_cache : bool, optional
            A boolean designating whether or not the docker build should use
            the cache.

        Returns
        -------
        Image
            The created image.

        Raises
        -------
        CalledProcessError
            If the docker build command fails.
        ValueError
            If both `dockerfile` and `dockerfile_string` are defined.
        """
        ...

    @overload
    @classmethod
    def build(
        cls: Type[Self],
        tag: str,
        *,
        dockerfile_string: str,
        context: Optional[os.PathLike[str]],
        stdout: Optional[io.TextIOBase],
        stderr: Optional[io.TextIOBase],
        network: str,
        no_cache: bool
    ) -> Self:
        """
        Builds a new image from a string in dockerfile syntax.

        Parameters
        ----------
        tag : str
            A name for the image.
        dockerfile_string : str
            A Dockerfile-formatted string.
        context : os.PathLike or None, optional
            The build context. Defaults to ".".
        stdout : io.TextIOBase or None, optional
            A file-like object that the stderr output of the docker build
            program will be redirected to to. If None, no redirection will
            occur. Defaults to None.
        stderr : io.TextIOBase or None, optional
            A file-like object that the stderr output of the docker build
            program will be redirected to. If None, no redirection will occur.
            It should be noted that docker build primarily outputs to stderr.
            Defaults to None.
        network : str, optional
            The name of the network. Defaults to "host".
        no_cache : bool, optional
            A boolean designating whether or not the docker build should use
            the cache.

        Returns
        -------
        Image
            The created Image.

        Raises
        -------
        CalledProcessError
            If the docker build command fails.
        ValueError
            If both `dockerfile` and `dockerfile_string` are defined.
        """
        ...

    @classmethod
    def build(
        cls,
        tag,
        *,
        dockerfile=None,
        dockerfile_string=None,
        context=".",
        stdout=None,
        stderr=None,
        network="host",
        no_cache=True
    ):
        if dockerfile is not None and dockerfile_string is not None:
            raise ValueError(
                "Both dockerfile and dockerfile_string passed as arguments."
            )

        # Build with dockerfile if dockerfile_string is None
        dockerfile_build = dockerfile_string is None

        context_str = os.fspath(".") if context is None else os.fspath(context)
        cmd = [
            "docker",
            "build",
            f"--network={network}",
            context_str,
            f"-t={tag}"
        ]

        if no_cache:
            cmd += ["--no-cache"]

        if dockerfile_build:
            # If a dockerfile path is given, include it.
            # Else, docker build will default to "./Dockerfile"
            if dockerfile is not None:
                cmd += [f"--file={os.fspath(dockerfile)}"]
            stdin = None
        else:
            cmd += ["-f-"]
            stdin = dockerfile_string

        run(
            cmd,
            text=True,
            stdout=stdout,  # type: ignore
            stderr=stderr,  # type: ignore
            input=stdin
        )

        return cls(tag)

    def _inspect(self, format: Optional[str] = None) -> str:
        """
        Use 'docker inspect' to retrieve a piece of information about the
        image.

        Parameters
        ----------
        format : str, optional
            The value to be requested by the --format argument, or None.
            Defaults to None.

        Returns
        -------
        str
            The string returned by the docker inspect command.

        Raises
        -------
        CalledProcessError
            If the docker inspect command fails.
        """
        cmd = ["docker", "inspect"]
        if format:
            cmd += [f"-f={format}"]
        cmd += [self._id]

        inspect_result = run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        output_text = inspect_result.stdout
        return output_text

    def run(
        self,
        command: str,
        *,
        stdout: Optional[Union[io.TextIOBase, int]] = None,
        stderr: Optional[Union[io.TextIOBase, int]] = None,
        interactive: bool = False,
        network: str = "host"
    ):
        """
        Run the given command on a container.

            .. note::
        For stderr special values to pass into `stdout` and `stdin`, review
        values passable into the same arguments in the :func:`subprocess.run`
        function:
        https://docs.python.org/3/library/subprocess.html#subprocess.run

            .. warning::
        This method does not work correctly if the image built does not have
        bash installed.

        Parameters
        ----------
        cmd : str
            The desired command, in linux command format.
        stdout : io.TextIOBase or subprocess special value or None, optional
            The location to send the process stdout output to. Defaults to None.
        stderr : io.TextIOBase or subprocess special value or None, optional
            The location to send the process stderr output to.
            Defaults to None.
        interactive : bool, optional
            A boolean describing whether or not to run this command in
            interactive mode or not. Defaults to True.
        network : str, optional
            The name of the network. Defaults to "host".

        Returns
        -------
        str, optional
            The output of the process, if `stdout` == PIPE.

        Raises
        -------
        CalledProcessError
            If the docker inspect command fails.
        CommandNotFoundOnImageError:
            When a command is attempted that is not recognized on the image.
        """
        cmd = ["docker", "run", f"--network={network}", "--rm"]
        if interactive:
            cmd += ["-i"]
            if stdin.isatty():
                cmd += ["--tty"]
        cmd += [self._id, "bash"]
        cmd += ["-ci"] if interactive else ["-c"]
        cmd += split(f"'{command}'")

        try:
            result = run(
                cmd,
                text=True,
                stdout=stdout,  # type: ignore
                stderr=stderr,  # type: ignore
                check=True
            )
            retval = result.stdout
        except CalledProcessError as err:
            if err.returncode == 127:
                raise CommandNotFoundOnImageError(err, split(command)[0])
            else:
                raise err
        return retval

    def check_command_availability(self, commands: Sequence[str]) -> List[str]:
        """
        Determines which of the commands in a list are present on the image.

        Parameters
        ----------
        commands : Sequence[str]
            A sequence of strings containing the names of commands to be
            checked for.

        Returns
        -------
        List[str]
            The names of all commands in `commands` that were present on the
            image.

        Raises
        -------
        CalledProcessError
            If the docker inspect command fails with a return value != 1.
        """
        found_commands = []
        for command_name in commands:
            try:
                command = self.run(
                    f"command -v {command_name}",
                    stdout=PIPE
                )
                if command_name in command and \
                        command_name not in found_commands:
                    found_commands += [command_name]
            except CalledProcessError as err:
                # "command -v {cmd}" returns 0 if the command is found, else 1.
                # Thus, the CalledProcessError exception can be ignored
                # if err.returncode == 1.
                # In other cases, the error still needs to be thrown.
                if err.returncode == 1:
                    pass
                else:
                    raise err
        return found_commands

    @property
    def tags(self) -> List[str]:
        """
        The Repo Tags held on this docker image.

        Returns
        -------
        List[str]
            The set of tags associated with this Image.

        Raises
        -------
        CalledProcessError
            If the docker inspect command fails.
        """
        return self._inspect(format="{{.RepoTags}}").strip('][\n').split(', ')

    @property
    def id(self) -> str:
        """
        This image's ID.

        Returns
        -------
        str
            This docker image's ID.

        Raises
        -------
        CalledProcessError
            If the docker inspect command fails.
        """
        return self._id

    def __repr__(self) -> str:
        """
        Returns a string representation of the Image.

        Returns
        -------
        str
            A string representation of the Image.
        """
        return f"Image(id={self._id}, tags={self.tags})"

    def __eq__(self, other: Any) -> bool:
        """
        Evaluates equality of an Image with another object.

        Parameters
        ----------
        other : any
            Another object to which this image will be compared.

        Returns
        -------
        boolean
            True if other is an Image with the same ID as this one, False
            otherwise.
        """
        if not isinstance(self, type(other)):
            return False
        return self._id == other._id


def get_image_id(name_or_id: str) -> str:
    """
    Acquires the ID of a docker image with the given name or ID.

    Parameters
    ----------
    name_or_id : str
        The image name or ID.

    Returns
    -------
    str
        The ID of the given docker image.

    Raises
    -------
    CalledProcessError
        If the docker inspect command fails.
    ValueError
        If `name_or_id` is not a string
    """
    if not isinstance(name_or_id, str):
        raise ValueError(
            f"name_or_id given as {type(name_or_id)}. Expected string."
        )
    command = "docker inspect -f={{.Id}} " + name_or_id
    process = run(
        split(command),
        capture_output=True,
        text=True,
        check=True
    )
    process_stdout = process.stdout.strip()
    return process_stdout
