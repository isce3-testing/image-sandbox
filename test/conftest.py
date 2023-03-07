import os


def pytest_sessionstart(session):
    cwd = os.fspath(os.getcwd())
    if cwd.endswith("image_and_tests"):
        os.chdir("test")


def pytest_sessionfinish(session, exitstatus):
    cwd = os.fspath(os.getcwd())
    testfile_path = "testfile.txt"
    if cwd.endswith("image_and_tests"):
        testfile_path = "test/" + testfile_path
    if os.path.isfile(testfile_path):
        os.remove(testfile_path)
