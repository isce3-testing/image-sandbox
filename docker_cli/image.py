import io
import os
from shlex import split
from subprocess import PIPE, STDOUT, CalledProcessError, run
from sys import stdin
from typing import (Any, List, Optional, Sequence, Type, TypeVar, Union,
                    overload)

from .exceptions import CommandNotFoundOnImageError


class Image:
    """A class which holds a reference to a given docker image and provides
    an interface by which to interact with that image.

    -   Capable of building docker images from dockerfiles or dockerfile-
        formatted strings via the build classmethods.
    -   Capable of acquiring information about the given image (see property
        methods below).
    -   Capable of running commands on containers built from the image using
        the run method.
    -   All docker build and run methods on the class can recive a file-like
        object, (io.TextIOBase or some subclass of it,) and they will write the
        outputs from docker into the file to enable logging.

    NOTE: This class does not work correctly if the image built does not have
        bash installed.
    """
    Self = TypeVar("Self", bound="Image")

    def __init__(self, name_or_id: str):
        """Initialize this Image. Connects the class with its ID.

        Parameters
        ----------
        name_or_id : str
            A name or ID by which to find this image using docker inspect.
        """
        self._id = get_image_id(name_or_id)

    @overload
    @classmethod
    def build(
        cls: Type[Self],
        context: os.PathLike[str],
        tag: str,
        *,
        dockerfile: os.PathLike[str],
        output_file: Optional[io.TextIOBase],
        network: str
    ):
        """Build a Dockerfile at the given path with the given name, then
        return the associated Image instance.

        Parameters
        ----------
        context : str
            The path to the file containing the Dockerfile
        tag : str
            A name for the image
        dockerfile : os.PathLike, optional
            The location of the Dockerfile to build, relative to the position
            held at the context argument described above.
        output_file : io.TextIOBase, optional
            A file-like object that the stderr output of the docker build
            program will be written to. If None, the method will not output to
            a file. Defaults to None.
        network : str
            The name of the network associated with the docker image to be
            built. Defaults to "host"

        Returns
        -------
        Image
            An Image class instance that references a Docker image built from
            the Dockerfile at context/dockerfile

        Raises
        -------
        CalledProcessError
            Raised if the docker build command fails. Holds the value returned
            by the docker build command in its returncode attribute, if not 0.
        """
        ...

    @overload
    @classmethod
    def build(
        cls: Type[Self],
        context: os.PathLike[str],
        tag: str,
        *,
        dockerfile_string: str,
        output_file: Optional[io.TextIOBase],
        network: str
    ):
        """Build a Dockerfile at the given path with the given name, then
        return the associated Image instance.

        Parameters
        ----------
        context : str
            The path to the file containing the Dockerfile
        tag : str
            A name for the image
        dockerfile_string : str
            A Dockerfile-formatted string containing the information necessary
            to build the desired image.
        output_file : io.TextIOBase, optional
            A file-like object that the stderr output of the docker build
            program will be written to. If None, the method will not output to
            a file. Defaults to None.
        network : str
            The name of the network associated with the docker image to be
            built. Defaults to "host"

        Returns
        -------
        Image
            An Image class instance that references a Docker image built from
            the Dockerfile-formatted string at context/dockerfile_loc

        Raises
        -------
        CalledProcessError
            Raised if the docker build command fails. Holds the value returned
            by the docker build command in its returncode attribute, if not 0.
        """
        ...

    @classmethod
    def build(
        cls,
        context,
        tag,
        *,
        dockerfile=None,
        dockerfile_string=None,
        output_file=None,
        network="host"
    ):
        if dockerfile is not None:
            dockerfile_build = True
        elif dockerfile_string is not None:
            dockerfile_build = False
        else:
            return ValueError("Image.build: either dockerfile or " +
                              "dockerfile_string must be defined.")

        if output_file is not None:
            run_stdout = output_file
        else:
            run_stdout = PIPE

        context_str = os.fspath(context)
        cmd = ["docker", "build", f"--network={network}", context_str]
        cmd += ["-t", tag]

        if dockerfile_build:
            cmd += [f"--file={os.fspath(dockerfile)}"]
            stdin_input = None
        else:
            cmd += ["-f-"]
            stdin_input = dockerfile_string

        run(
            cmd,
            text=True,
            stdout=run_stdout,  # type: ignore
            stderr=STDOUT,
            input=stdin_input
        )

        return cls(tag)

    def _inspect(self, format: Optional[str] = None) -> str:
        """Private method. Use 'docker inspect' to retrieve a piece of
        information about the Docker image referenced by this instance.

        Parameters
        ----------
        format : str, optional
            The value to be requested by the --format argument of docker
            inspect, or "". If this string is non-empty, the docker inspect
            command will be called with "-f=this_value". Defaults to "".

        Returns
        -------
        str
            The string returned by the docker inspect command.

        Raises
        -------
        CalledProcessError
            Raised if the docker inspect command fails. Holds the value
            returned by the docker inspect command in its returncode attribute,
            if not 0.
        """
        cmd = ["docker", "inspect"]
        if format:
            cmd += [f"-f={format}"]
        cmd += [self._id]
        inspect_result = run(
            cmd,
            capture_output=True,
            text=True,
            check=True)
        output_text = inspect_result.stdout
        return output_text

    def run(
        self,
        command: str,
        *,
        stdout: Union[io.TextIOBase, int] = PIPE,
        stderr: Union[io.TextIOBase, int] = STDOUT,
        interactive: bool = False,
        network: str = "host"
    ):
        """Run the given command on a container spun up on this image. Redirect
        stdout and stderr to given file-like objects or subprocess locations

        Parameters
        ----------
        cmd : str
            The desired command, in linux command format.
        stdout : io.TextIOBase or subprocess.PIPE
            The location to send the process stdout output to. If set to
            subprocess.PIPE, this method will return a string containing
            the stdout output. Defaults to subprocess.PIPE
        stderr : io.TextIOBase or subprocess special value or None
            The location (file-like object or pipe) to send the process stderr
            output to. If set to subprocess.DEVNULL or None, error messages
            will be discarded. If set to subprocess.STDOUT, the output of this
            run's stderr will be interleaved with stdout. Defaults to
            subprocess.STDOUT
        interactive : bool, optional
            A boolean describing whether or not to run this command in
            interactive mode or not. True for interactive, False for
            non-interactive. Defaults to True.
        network : str
            The name of the network associated with the docker command to be
            run. Defaults to "host"

        Returns
        -------
        str, optional
            The stdout of the process run on the container, if stdout was set
            to PIPE

        Raises
        -------
        CalledProcessError
            Raised if the docker run command fails. Holds the value returned by
            the docker run command in its returncode attribute.
        CommandNotFoundOnImageError:
            A subclass of CalledProcessError. Is thrown when this method
            attempts to run a command on a docker image and that command
            does not exist within the image.
        """
        cmd = ["docker", "run", f"--network={network}", "--rm"]
        if interactive:
            cmd += ["-i"]
            if stdin.isatty():
                cmd += ["--tty"]
        cmd += [self._id, "bash"]
        cmd += ["-ci"] if interactive else ["-c"]
        cmd += split(f"'{command}'")

        if stdout is not None:
            run_stdout = stdout
        else:
            run_stdout = PIPE

        if stderr is not None:
            run_stderr = stderr
        else:
            run_stderr = STDOUT

        try:
            result = run(
                cmd,
                text=True,
                stdout=run_stdout,  # type: ignore
                stderr=run_stderr,  # type: ignore
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
        """Determines which of the commands in a list are present on the image.

        Parameters
        ----------
        commands : Sequence[str]
            A sequence of strings containing the names of commands to be
            checked for.

        Returns
        -------
        List[str]
            The names of all commands in cmd_list that were present on the
            image.
        """
        found_commands = []
        for command_name in commands:
            try:
                command = self.run(f"command -v {command_name}")
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
        """Returns the Repo Tags held on this docker image

        Returns
        -------
        List[str]
            A list containing the set of tags associated with this docker Image

        Raises
        -------
        CalledProcessError
            See _inspect method
        """
        return self._inspect(format="{{.RepoTags}}").strip('][\n').split(', ')

    @property
    def id(self) -> str:
        """Returns this image's ID

        Returns
        -------
        str
            This docker image's ID
        """
        return self._id

    def __repr__(self) -> str:
        """Returns a string representation of the Image formatted as
        "Image(id=_id, tags=tags)".

        Returns
        -------
        str
            A string representation of the Image.
        """
        return f"Image(id={self._id}, tags={self.tags})"

    def __eq__(self, other: Any) -> bool:
        """Evaluates equality of an Image with another object.
        Two Images are the same if and only if their ID's are the same.
        Any other object will evaluate as False.

        Parameters
        ----------
        other : any
            Another object to which this image will be compared

        Returns
        -------
        boolean
            True if:
                other is an Image with the same ID as this one
            False otherwise
        """
        if not isinstance(self, type(other)):
            return False
        return self._id == other._id


def get_image_id(name_or_id: str) -> str:
    """Acquires the ID of a docker image with the given name or ID and returns
    it as a string

    Parameters
    ----------
    name_or_id : str
        A name or ID by which to find the docker image

    Returns
    -------
    str
        A string containing the ID of the given docker image

    Raises
    -------
    CalledProcessError
        Raised if the docker inspect command fails. Holds the value returned by
        the docker inspect command in its returncode attribute, if not 0.
    """
    command = "docker inspect -f={{.Id}} " + f"{name_or_id}"
    process = run(split(command), capture_output=True, text=True, check=True)
    process_stdout = process.stdout.strip()
    return process_stdout
