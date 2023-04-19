import io
import os
from typing import Dict, List, Optional, Type, TypeVar, Union

from ._exceptions import DockerBuildError
from ._image import Image


class Dockerfile:
    """
    A dockerfile header and body.

    The header is any text prior to the main FROM line.
    The body is any text following the FROM line.
    Capabilities include:
    -   Combining dockerfiles together.
    -   Returning a string representation of the dockerfile with a given
        base image
    -   Building a docker image from a given base image
    -   Appending and prepending to the body and header
    """

    Self = TypeVar("Self", bound="Dockerfile")

    def __init__(
        self,
        body: str,
        *,
        header: Optional[str] = ""
    ):
        self._header = header
        self._body = body

    @classmethod
    def combine_dockerfiles(
        cls: Type[Self],
        dockerfile_1: Self,
        dockerfile_2: Self
    ) -> Self:
        """
        Combines two dockerfiles into one.

        Parameters
        ----------
        cls : Self
            The Dockerfile class
        dockerfile_1 : Dockerfile
            The dockerfile whose header and body will be first.
        dockerfile_2 : Dockerfile
            The dockerfile whose header and body will be last.

        Returns
        -------
        Dockerfile
            The resulting dockerfile.
        """
        assert isinstance(dockerfile_1.body, str)
        assert isinstance(dockerfile_2.body, str)
        body = dockerfile_1.body + "\n" + dockerfile_2.body
        assert isinstance(dockerfile_1._header, str)
        assert isinstance(dockerfile_2._header, str)
        header = dockerfile_1._header + "\n" + dockerfile_2._header
        return cls(body=body, header=header)

    def full_dockerfile(
        self,
        parent: str
    ) -> str:
        """
        Returns a full dockerfile string with the given parent image.

        Parameters
        ----------
        parent : str
            The parent image name.

        Returns
        -------
        str
            The dockerfile encoded string.
        """

        from_line = "FROM " + parent + "\n\n"

        header = (self._header + "\n") if self._header else ""

        return header + from_line + self._body

    def build(
        self,
        tag: str,
        base: str,
        context: Union[str, os.PathLike[str]] = ".",
        stdout: Optional[io.TextIOBase] = None,
        stderr: Optional[io.TextIOBase] = None,
        network: str = "host",
        no_cache: bool = False
    ) -> Image:
        """
        Builds this dockerfile with the

        Parameters
        ----------
        tag : str
            The tag of the image to be built.
        base : str
            The tag of the image on which the built image will be based.
        context : os.PathLike[str], optional
            The context path of the image. By default ".".
        stdout : io.TextIOBase, optional
            A file to redirect the stdout output of the build command to.
            If None, no redirection will occur. By default None.
        stderr : io.TextIOBase, optional
            A file to redirect the stderr output of the build command to.
            If None, no redirection will occur. By default None.
        network : str, optional
            The name of the network. By default "host".
        no_cache : bool, optional
            Whether or not to use the cache when building this image.
            By default False.

        Returns
        -------
        Image
            The Image object that was built.
        """
        full_file = self.full_dockerfile(parent=base)
        try:
            image = Image.build(
                tag=tag,
                context=context,
                dockerfile_string=full_file,
                stdout=stdout,
                stderr=stderr,
                network=network,
                no_cache=no_cache
            )
        except DockerBuildError as err:
            raise DockerBuildError(
                message="Failed to build docker image from the following dockerfile:\n"
                        "##################\n"
                        f"{full_file}\n"
                        "##################\n"
            ) from err
        return image

    def prepend_body(self, prefix: str):
        """
        Prepends a string onto the body of the dockerfile.

        Parameters
        ----------
        prefix : str
            The string to be prepended.
        """
        self._body = prefix + "\n" + self._body

    def append_body(self, text: str):
        """
        Appends a string onto the body of the dockerfile.

        Parameters
        ----------
        text : str
            The string to be appended.
        """
        self._body += "\n" + text

    def prepend_header(self, prefix: str):
        """
        Prepends a string onto the header of the dockerfile.

        Parameters
        ----------
        prefix : str
            The string to be prepended.
        """
        assert isinstance(self._header, str)
        self._header = prefix + "\n" + self._header

    def append_header(self, text: str):
        """
        Appends a string onto the header of the dockerfile.

        Parameters
        ----------
        text : str
            The string to be appended.
        """
        assert isinstance(self._header, str)
        self._header += "\n" + text

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, value: str):
        assert isinstance(value, str)
        self._body = value

    @property
    def header(self):
        return self._header

    @header.setter
    def header(self, value: str):
        assert isinstance(value, str)
        self._header = value


class _TaggedDockerfile:  # pragma: no cover
    """
    Holds information about a tagged Dockerfile object.
    """

    def __init__(
            self,
            dockerfile: Dockerfile,
            image_tag: str,
            no_cache: bool = False
    ):
        self.dockerfile = dockerfile
        self.image_tag = image_tag
        self.no_cache = no_cache


class StagedDockerfileList:  # pragma: no cover
    """
    A list of tagged dockerfiles, with each being a parent to the next.

    Capabilities include:
    -   Appending a dockerfile to the end of the list
    -   Building the list of dockerfiles
    -   Returning the initial dockerfile in the list
    """

    def __init__(self, origin_image: str = "oraclelinux:8.4"):
        self._tagged_dockerfiles: List[_TaggedDockerfile] = []
        self.origin_name = origin_image

    def append(
        self,
        dockerfile: Dockerfile,
        image_tag: str,
        no_cache: bool = False
    ) -> None:
        """
        Append a dockerfile to the end of the list.

        Parameters
        ----------
        dockerfile : Dockerfile
            The dockerfile to be appended.
        image_tag : str
            The tag that the dockerfile will be given when built.
        no_cache : bool, optional
            Whether or not the dockerfile is to be built with cache off.
            Defaults to False.
        """
        tagged_dockerfile = _TaggedDockerfile(
            dockerfile=dockerfile,
            image_tag=image_tag,
            no_cache=no_cache
        )
        self._tagged_dockerfiles.append(tagged_dockerfile)

    def _build_dockerfile(
        self,
        tagged_dockerfile: _TaggedDockerfile,
        parent: str,
        stdout: Optional[io.TextIOBase] = None,
        stderr: Optional[io.TextIOBase] = None
    ) -> Image:
        """
        Build a single tagged dockerfile.

        Parameters
        ----------
        tagged_dockerfile : TaggedDockerfile
            The dockerfile, with associated tag information.
        parent : str
            The parent of the dockerfile.
        stdout : io.TextIOBase, optional
            A file to redirect the stdout output of the build command to.
            If None, no redirection will occur. By default None.
        stderr : io.TextIOBase, optional
            A file to redirect the stderr output of the build command to.
            If None, no redirection will occur. By default None.

        Returns
        -------
        Image
            The built image.
        """
        dockerfile = tagged_dockerfile.dockerfile
        return dockerfile.build(
            tag=tagged_dockerfile.image_tag,
            base=parent,
            context=".",
            stdout=stdout,
            stderr=stderr,
            no_cache=tagged_dockerfile.no_cache
        )

    def build(
        self,
        stdout: Optional[io.TextIOBase] = None,
        stderr: Optional[io.TextIOBase] = None
    ) -> Dict[str, Image]:
        """
        Builds the staged list of dockerfiles.

        Parameters
        ----------
        stdout : io.TextIOBase, optional
            A file to redirect the stdout output of the build command to.
            If None, no redirection will occur. By default None.
        stderr : io.TextIOBase, optional
            A file to redirect the stderr output of the build command to.
            If None, no redirection will occur. By default None.

        Returns
        -------
        Dict[str, Image]
            A dictionary of images built, indexed by their tags.
        """
        images = {}

        image = self._build_dockerfile(
            tagged_dockerfile=self._tagged_dockerfiles[0],
            parent=self.origin_name,
            stdout=stdout, stderr=stderr
        )

        images[self._tagged_dockerfiles[0].image_tag] = image

        for layer in range(1, len(self._tagged_dockerfiles)):
            tag_dkf = self._tagged_dockerfiles[layer]
            parent_name = self._tagged_dockerfiles[layer - 1].image_tag

            image = self._build_dockerfile(
                tagged_dockerfile=tag_dkf,
                parent=parent_name,
                stdout=stdout, stderr=stderr
            )

            images[tag_dkf.image_tag] = image

        return images

    @property
    def initial_dockerfile(self) -> Optional[Dockerfile]:
        """
        Returns the first dockerfile in the list, if any.

        Returns
        -------
        Dockerfile | None
            The dockerfile, if there is one. Else, None.
        """
        if len(self._tagged_dockerfiles) > 0:
            return self._tagged_dockerfiles[0].dockerfile
        else:
            return None
