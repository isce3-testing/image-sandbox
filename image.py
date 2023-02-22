import io
from shlex import split
from subprocess import CalledProcessError, run
from sys import stdin
from typing import Union

from exceptions import CommandNotFoundOnImageError


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

    def __init__(self, name_or_id: str):
        """Initialize this Image. Connects the class with its ID.

        Parameters
        ----------
        name_or_id : str
            A name or ID by which to find this image using docker inspect.
        """
        self._id = get_image_id(name_or_id)

    @classmethod
    def build_from_dockerfile(
        cls,
        context: str,
        tag: str,
        output_file: Union[io.TextIOBase, None] = None,
        dockerfile_loc: str = ""
    ):
        """Build a Dockerfile at the given path with the given name, then
        return the associated Image instance.

        Parameters
        ----------
        context : str
            The path to the file containing the Dockerfile
        tag : str
            A name for the image
        output_file : io.TextIOBase or None
            A file-like object that the sterr output of the docker build
            program will be written to. If None, the method will not output to
            a file. Defaults to None.
        dockerfile_loc : str
            The location of the Dockerfile to build, relative to the position
            held at the context argument described above. If empty, the command
            is called assuming that the dockerfile is held at the context root
            folder. Defaults to "".

        Returns
        -------
        Image
            An Image class instance that references a Docker image built from
            the Dockerfile at context/dockerfile_loc

        Raises
        -------
        CalledProcessError
            Raised if the docker build command fails. Holds the value returned
            by the docker build command in its returncode attribute, if not 0.
        """

        if dockerfile_loc:
            dockerfile_arg = f" --file='{dockerfile_loc}'"
        else:
            dockerfile_arg = ""

        command = "docker build --network=host " + \
            f"{context}{dockerfile_arg} -t {tag}"
        process = run(
            split(command),
            check=True,
            text=True,
            capture_output=True)

        if output_file is not None and isinstance(output_file, io.TextIOBase):
            output_file.write(process.stderr)

        return cls(tag)

    @classmethod
    def build_from_string(
        cls,
        context: str,
        tag: str,
        dockerfile_string: str,
        output_file: Union[io.TextIOBase, None] = None
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
        output_file : io.TextIOBase or None
            A file-like object that the sterr output of the docker build
            program will be written to. If None, the method will not output to
            a file. Defaults to None.

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
        command = f"docker build --network=host -f- -t {tag} {context}"
        process = run(
            split(command),
            input=dockerfile_string,
            text=True,
            capture_output=True,
            check=True)

        if output_file is not None and isinstance(output_file, io.TextIOBase):
            output_file.write(process.stderr)

        return cls(tag)

    def _inspect(self, format: str = ""):
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
        format_block = f" -f={format}" if format else ""
        command = f"docker inspect{format_block} {self._id}"

        process = run(
            split(command),
            capture_output=True,
            text=True,
            check=True)
        output_text = process.stdout
        return output_text

    def run(
        self,
        cmd: str,
        output_file: Union[io.TextIOBase, None] = None,
        interactive: bool = True
    ):
        """Run the given command on a container spun up on this image.

        Parameters
        ----------
        cmd : str
            The desired command, in linux command format.
        output_file : io.TextIOBase or None
            A file-like object that the stdout output of the docker run program
            will be written to. If None, the method will not output to a file.
            Defaults to None.
        interactive : bool, optional
            A boolean describing whether or not to run this command in
            interactive mode or not. True for interactive, False for
            non-interactive. Defaults to True.

        Returns
        -------
        str
            The stdout of the process run on the container.

        Raises
        -------
        CalledProcessError
            Raised if the docker run command fails. Holds the value returned by
            the docker run command in its returncode attribute.
        """
        docker_args = ""
        if interactive:
            docker_args += " -i"
            if stdin.isatty():
                docker_args += " --tty"
        bash_args = " -ci" if interactive else " -c"
        command = f"docker run {docker_args} --network=host --rm " + \
            f"{self._id} bash{bash_args} '{cmd}'"
        try:
            process = run(
                split(command),
                check=True,
                capture_output=True,
                text=True)
        except CalledProcessError as err:
            if err.returncode == 127:
                raise CommandNotFoundOnImageError(err, cmd.split()[0])
            else:
                raise err
        output_text = process.stdout

        if output_file is not None and isinstance(output_file, io.TextIOBase):
            output_file.write(output_text)

        return output_text

    def check_command_availability(self, cmd_list: list) -> list:
        """Determines which of the commands in a list are present on the image.

        Parameters
        ----------
        cmd_list : list
            A list of strings containing the names of commands to be
            checked for.

        Returns
        -------
        list[str]
            The names of all commands in cmd_list that were present on the
            image.
        """
        command = ""
        found_commands = []
        for command_name in cmd_list:
            try:
                command = self.run(f"command -v {command_name}")
                if command_name in command and \
                        command_name not in found_commands:
                    found_commands.append(command_name)
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
    def tags(self):
        """Returns the Repo Tags held on this docker image

        Returns
        -------
        str
            A string containing the repo tags returned by a docker inspect
            command on this image

        Raises
        -------
        CalledProcessError
            See _inspect method
        """
        return self._inspect(format="{{.RepoTags}}").strip()

    @property
    def id(self):
        """Returns this image's ID

        Returns
        -------
        str
            This docker image's ID
        """
        return self._id

    def __repr__(self):
        """Returns a string representation of the Image formatted as
        "Image(id=_id, tags=tags)".

        Returns
        -------
        str
            A string representation of the Image.
        """
        return f"Image(id={self._id}, tags={self.tags})"

    def __eq__(self, other):
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


def get_image_id(name_or_id: str):
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
