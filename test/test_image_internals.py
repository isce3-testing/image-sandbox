from shlex import split
from subprocess import CalledProcessError, run

import pytest

from docker_cli.image import Image


def test_inspect():
    """Tests that the _inspect method correctly retrieves data from the docker
    image."""
    run(split("docker build . -t test"))
    inspect_process = run(
        split("docker inspect -f='{{.RepoTags}}' test"),
        capture_output=True,
        text=True,
        check=True,
    )
    tags = inspect_process.stdout.strip()

    img: Image = Image("test")
    img_tags = img._inspect(format="{{.RepoTags}}").strip()
    assert img_tags == tags

    run(split("docker image remove test"))


def test_inspect_malformed():
    """Tests that the _inspect method correctly raises a CalledProcessError
    when a malformed string is passed to it"""
    run(split("docker build . -t test"))

    img: Image = Image("test")
    with pytest.raises(CalledProcessError):
        img._inspect(format="{{.MalformedInspect}}").strip()

    run(split("docker image remove test"))