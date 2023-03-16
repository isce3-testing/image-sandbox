from subprocess import CalledProcessError


class CommandNotFoundError(CalledProcessError):
    def __init__(self, prior_error: CalledProcessError, command_name: str):
        super(CommandNotFoundError, self).__init__(
            prior_error.returncode,
            prior_error.cmd
        )
        self.command_name = command_name

    def __str__(self):
        return f"Command '{self.command_name}' was run, but is not " + \
            "present on the Docker image."


class DockerBuildError(Exception):
    """Raised when a docker image fails to build"""

    def __init__(self, image_tag: str, dockerfile: str, message: str = ""):
        if message:
            self.message = message
        else:
            self.message = f"Docker image {image_tag} failed to build with " +\
                           f"dockerfile:\n{dockerfile}."

    def __str__(self):
        return self.message


class ImageNotFoundError(Exception):
    """
    Raised when attempting to create an image using a tag or ID that does not
    exist.
    """

    def __init__(self, tag_or_id: str, message: str = ""):
        if message:
            self.message = message
        else:
            self.message = f"Docker image \"{tag_or_id}\" not found."

    def __str__(self):
        return self.message
