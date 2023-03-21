from typing import Optional, overload


class CommandNotFoundError(Exception):
    """Raised when a command is attempted but not found."""

    def __init__(self, command_name: str):
        """
        Raise this exception when a command is attempted but not found.

        Parameters
        ----------
        command_name : str
            The name of the command.
        """
        self.command_name = command_name
        super(CommandNotFoundError, self).__init__(
            f"Command '{self.command_name}' was run, but is not "
            "present on the Docker image."
        )


class DockerBuildError(Exception):
    """Raised when a docker image fails to build"""

    @overload
    def __init__(self, *, message: Optional[str]):
        """
        Raise this exception when a docker image fails to build.

        Parameters
        ----------
        message : str
            The error message.
        """
        ...

    @overload
    def __init__(self, *, image_tag: Optional[str], dockerfile: Optional[str]):
        """
        Raise this exception when a docker image fails to build.

        Parameters
        ----------
        image_tag : str
            The tag of the image.
        dockerfile : str
            The dockerfile used to build the image.
        """
        ...

    def __init__(
        self,
        *,
        message: Optional[str] = None,
        image_tag: Optional[str] = None,
        dockerfile: Optional[str] = None
    ):
        if (dockerfile is not None) or (image_tag is not None):
            if message is not None:
                raise ValueError("'message' argument passed with one or both of "
                                 "'dockerfile' and 'image_tag.")
            elif dockerfile is None:
                raise ValueError("'image_tag' passed without 'dockerfile'.")
            elif image_tag is None:
                raise ValueError("'dockerfile' passed without 'image_tag'.")
            else:
                super(DockerBuildError, self).__init__(
                    DockerBuildError,
                    f"Docker image {image_tag} failed to build with "
                    f"dockerfile:\n{dockerfile}.")
        elif message is not None:
            super(DockerBuildError, self).__init__(message)
        else:
            raise ValueError("No values passed. Either 'message' or both of"
                             "'dockerfile' and 'image_tag' required.")


class ImageNotFoundError(Exception):
    """
    Raised when attempting to create an image using a tag or ID that does not
    exist.
    """

    @overload
    def __init__(self, *, message: str):
        """
        Raise this exception when unable to find an image.

        Parameters
        ----------
        message : str
            The error message.
        """
        ...

    @overload
    def __init__(self, *, tag_or_id: str):
        """
        Raise this exception when unable to find an image.

        Parameters
        ----------
        tag_or_id : str
            The tag or ID of the image.
        """
        ...

    def __init__(
        self,
        *,
        tag_or_id: Optional[str] = None,
        message: Optional[str] = None
    ):
        if message is not None:
            if tag_or_id is not None:
                raise ValueError("Use only one of 'message' or 'tag_or_id'.")
            super(ImageNotFoundError, self).__init__(message)
        elif tag_or_id is not None:
            super(ImageNotFoundError, self).__init__(
                f"Docker image \"{tag_or_id}\" not found."
            )
        else:
            raise ValueError("No values passed. Either 'message' or 'tag_or_id' "
                             "required.")
