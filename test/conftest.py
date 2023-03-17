import os
import sys
from pathlib import Path
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


def pytest_sessionstart(session):

    # Navigate to the test folder path in order to make use of tests that require for
    # a dockerfile to be in the local directory, regardless of where tests are being
    # run from.
    os.chdir(Path(__file__).parent)

    # Set the system to look for files in the repository root path so it can see the
    # docker_cli module without having to install it.
    sys.path.insert(0, str(Path(__file__).parents[1]))
