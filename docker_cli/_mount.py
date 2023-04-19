import os
from typing import Union


class Mount:
    """A description of a docker mount."""

    def __init__(
        self,
        host_mount_point: Union[os.PathLike[str], str],
        image_mount_point: Union[os.PathLike[str], str],
        permissions: str
    ):
        """
        A description of a docker mount.

        Parameters
        ----------
        host_mount_point : os.PathLike[str]
            The location of the mount in the host environment,
        image_mount_point : os.PathLike[str]
            The location of the mount on the image,
        permissions : str
            "ro" for readonly, "rw" for read/write.

        Raises
        ------
        ValueError
            _description_
        """
        if permissions not in ["ro", "rw"]:
            raise ValueError(
                "Permissions value for mount not given as \"ro\" or \"rw\"."
            )
        self.permissions = permissions
        self.host_mount_point = host_mount_point
        self.image_mount_point = image_mount_point

    def mount_string(self) -> str:
        """
        Returns a string describing the mount.

        Returns
        -------
        str
            The string.
        """
        return f"{self.host_mount_point}:{self.image_mount_point}:{self.permissions}"
