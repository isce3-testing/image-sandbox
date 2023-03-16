import os
import sys
from pathlib import Path
from shlex import split
from subprocess import run

from pytest import fixture


@fixture
def test_image_id():
    """
    Builds an image for testing and returns its ID.
    """
    run(split("docker build . -t test"))
    inspect_process = run(
        split("docker inspect -f='{{.Id}}' test"),
        capture_output=True,
        text=True,
        check=True,
    )
    return inspect_process.stdout.strip()


def pytest_sessionstart(session):
    os.chdir(Path(__file__).parent)
    sys.path.insert(0, str(Path(__file__).parents[1]))


def pytest_sessionfinish(session, exitstatus):
    cwd = os.fspath(os.getcwd())
    testfile_path = "testfile.txt"
    if cwd.endswith("image_and_tests"):
        testfile_path = "test/" + testfile_path
    if os.path.isfile(testfile_path):
        os.remove(testfile_path)
