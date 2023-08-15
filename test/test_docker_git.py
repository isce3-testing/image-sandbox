from pathlib import Path
from subprocess import PIPE
from typing import Any, Tuple

from pytest import mark

from docker_cli._docker_git import git_extract_dockerfile
from docker_cli._image import Image
from docker_cli._url_reader import URLReader, get_supported_url_readers, get_url_reader

from .utils import generate_tag, rough_dockerfile_validity_check


@mark.dockerfiles
@mark.git
def test_git_dockerfile():
    """Performs a rough validity check of the Git dockerfile"""
    for supported_reader in get_supported_url_readers():
        url_reader = get_url_reader(supported_reader)
        dockerfile = git_extract_dockerfile(
            base="base",
            archive_url="www.url.com/a.tar.gz",
            directory="/",
            url_reader=url_reader,
        )
        rough_dockerfile_validity_check(dockerfile=dockerfile)


@mark.images
@mark.git
def test_docker_git(
    init_tag: str,
    init_image: Image,  # type: ignore
    base_properties: Tuple[Any, URLReader],
):
    # This is a basic github archive from octocat's test-repo1 archive.
    # If this test fails, one thing to do is check that this archive exists.
    archive = "https://github.com/octocat/test-repo1/archive/refs/tags/1.0.tar.gz"
    _, url_reader = base_properties
    img_tag = generate_tag("git-archive")

    dockerfile = git_extract_dockerfile(
        base=init_tag,
        archive_url=archive,
        directory=Path("/src/"),
        url_reader=url_reader,
    )

    image = Image.build(tag=img_tag, dockerfile_string=dockerfile, no_cache=True)

    # Test that three files, which should be present at the archive, are present and
    # in the right location.
    image.run("test -f /src/2015-04-12-test-post-last-year.md")
    image.run("test -f /src/2016-02-24-first-post.md")
    image.run("test -f /src/2016-02-26-sample-post-jekyll.md")