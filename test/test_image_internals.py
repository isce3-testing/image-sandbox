from shlex import split
from subprocess import CalledProcessError, run

import pytest

from docker_cli import Image


def test_inspect(test_image_id):
    """Tests that the _inspect method correctly retrieves data from the docker
    image."""
    inspect_process = run(
        split("docker inspect -f='{{.RepoTags}}' test"),
        capture_output=True,
        text=True,
        check=True,
    )
    tags = inspect_process.stdout.strip()

    img: Image = Image(test_image_id)
    img_tags = img._inspect(format="{{.RepoTags}}").strip()
    assert img_tags == tags

    run(split("docker image remove test"))


def test_inspect_malformed(test_image_id):
    """Tests that the _inspect method correctly raises a CalledProcessError
    when a malformed string is passed to it"""
    img: Image = Image(test_image_id)
    with pytest.raises(CalledProcessError):
        img._inspect(format="{{.MalformedInspect}}").strip()

    run(split("docker image remove test"))
