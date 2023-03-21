"""This file contains all fixtures that are needed by multiple test files."""

from shlex import split
from subprocess import run

from pytest import fixture


@fixture
def image_tag():
    """
    Returns an image tag

    Returns
    ------
    str
        An image tag
    """
    return "isce3_pytest_temp"


@fixture
def image_id(image_tag):
    """
    Builds an image for testing and returns its ID.

    Yields
    ------
    str
        An image ID.
    """
    run(split(f"docker build . -t {image_tag}"))
    inspect_process = run(
        split("docker inspect -f='{{.Id}}' " + image_tag),
        capture_output=True,
        text=True,
        check=True,
    )
    id = inspect_process.stdout.strip()
    yield id
    run(split(f"docker image remove {image_tag}"))
