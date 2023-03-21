import os
import sys
from pathlib import Path


def pytest_sessionstart(session):

    # Navigate to the test folder path in order to make use of tests that require for
    # a dockerfile to be in the local directory, regardless of where tests are being
    # run from.
    os.chdir(Path(__file__).parent)

    # Set the system to look for files in the repository root path so it can see the
    # docker_cli module without having to install it.
    sys.path.insert(0, str(Path(__file__).parents[1]))
