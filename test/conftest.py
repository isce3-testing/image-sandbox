import os
import sys
from pathlib import Path
from shlex import split
from subprocess import run

from pytest import fixture


@fixture
def image_id():
    """
    Builds an image for testing and returns its ID.
    """
    run(split("docker build . -t isce3_pytest_temp"))
    inspect_process = run(
        split("docker inspect -f='{{.Id}}' isce3_pytest_temp"),
        capture_output=True,
        text=True,
        check=True,
    )
    id = inspect_process.stdout.strip()
    yield id
    run(split(f"docker image remove {id}"))


def pytest_sessionstart(session):

    # Navigate to the test folder path in order to make use of tests that require for
    # a dockerfile to be in the local directory, regardless of where tests are being
    # run from.
    os.chdir(Path(__file__).parent)

    # Set the system to look for files in the repository root path so it can see the
    # docker_cli module without having to install it.
    sys.path.insert(0, str(Path(__file__).parents[1]))
