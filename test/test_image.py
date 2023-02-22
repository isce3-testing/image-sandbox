import os
from shlex import split
from subprocess import CalledProcessError, run

import pytest

from docker_cli.exceptions import CommandNotFoundOnImageError
from docker_cli.image import Image, get_image_id


@pytest.fixture
def test_image_id():
    run(split("docker build ./ -t test"))
    inspect_process = run(
        split("docker inspect -f='{{.Id}}' test"),
        capture_output=True,
        text=True,
        check=True,
    )
    return inspect_process.stdout.strip()


def test_init(test_image_id):
    """Tests that the __init__ function on the Image class is correctly
    receiving and remembering the ID of a docker image."""
    id = test_image_id
    print("ID: " + id)
    img = Image("test")

    assert img is not None
    assert img.id == id

    img_2 = Image(id)
    assert img_2.id == id

    run(split("docker image remove test"))


def test_init_CalledProcessError():
    """Tests that the __init__ function on the Image class is correctly
    returning a CalledProcessError when given a malformed name."""
    img = None
    with pytest.raises(CalledProcessError):
        img = Image("malformed_image_name_or_id")
    assert img is None


def test_build_from_dockerfile():
    """Tests that the build_from_dockerfile method correctly constructs a
    docker image and returns a properly-formatted Image instance."""
    img = Image.build_from_dockerfile(".", "test")
    inspect_process = run(
        split("docker inspect -f='{{.Id}}' test"),
        text=True,
        capture_output=True)
    id = inspect_process.stdout.strip()

    assert img is not None
    assert img.id == id
    run(split("docker image remove test"))


def test_build_from_dockerfile_output_to_file():
    """Tests that the build_from_dockerfile method correctly constructs a
    docker image and returns a properly-formatted Image instance."""
    file = open("testfile.txt", "w")
    img = Image.build_from_dockerfile(".", "test", output_file=file)
    inspect_process = run(
        split("docker inspect -f='{{.Id}}' test"),
        text=True,
        capture_output=True)
    id = inspect_process.stdout.strip()
    file.close()

    assert img is not None
    assert img.id == id
    assert os.stat("testfile.txt").st_size > 0

    os.remove("testfile.txt")
    run(split("docker image remove test"))


def test_build_from_dockerfile_dockerfile_in_different_location():
    """Tests that the build_from_dockerfile method can from a dockerfile in a
    different location than the context root directory."""
    img = Image.build_from_dockerfile(
        ".", "test", dockerfile_loc="dockerfiles/alpine_functional"
    )
    inspect_process = run(
        split("docker inspect -f='{{.Id}}' test"),
        text=True,
        capture_output=True)
    id = inspect_process.stdout.strip()

    assert img is not None
    assert img.id == id
    run(split("docker image remove test"))


def test_build_from_dockerfile_context_in_different_location():
    """Tests that the build_from_dockerfile method can build when the context
    is set to a different directory."""
    img = Image.build_from_dockerfile(
        "./dockerfiles",
        "test",
        dockerfile_loc="./dockerfiles/alpine_functional"
    )
    inspect_process = run(
        split("docker inspect -f='{{.Id}}' test"),
        text=True,
        capture_output=True)
    id = inspect_process.stdout.strip()

    assert img is not None
    assert img.id == id
    run(split("docker image remove test"))


def test_build_from_dockerfile_in_malformed_location():
    """Tests that the build_from_dockerfile method correctly raises a
    CalledProcessError when a malformed location is passed in."""
    img = None
    with pytest.raises(CalledProcessError):
        img = Image.build_from_dockerfile(
            ".",
            "test",
            dockerfile_loc="non_existant_directory/Dockerfile")
    assert img is None


def test_build_from_string():
    """Tests that the build_from_string method correctly builds and returns an
    Image when given a dockerfile-formatted string."""
    stdout: str = run(
        split("cat Dockerfile"),
        capture_output=True,
        text=True).stdout
    img: Image = Image.build_from_string(".", "test", stdout)
    inspect_process = run(
        split("docker inspect -f='{{.Id}}' test"),
        text=True,
        capture_output=True)
    id = inspect_process.stdout.strip()

    assert img is not None
    assert img.id == id
    run(split("docker image remove test"))


def test_build_from_string_output_to_file():
    """Tests that the build_from_dockerfile method correctly constructs a
    docker image and returns a properly-formatted Image instance."""
    file = open("testfile.txt", "w")
    stdout: str = run(
        split("cat Dockerfile"),
        capture_output=True,
        text=True).stdout
    img: Image = Image.build_from_string(".", "test", stdout, output_file=file)
    inspect_process = run(
        split("docker inspect -f='{{.Id}}' test"),
        text=True,
        capture_output=True)
    id = inspect_process.stdout.strip()
    file.close()

    assert img is not None
    assert img.id == id
    assert os.stat("testfile.txt").st_size > 0

    run(split("docker image remove test"))


def test_build_from_malformed_string():
    """Tests that the build_from_string method correctly raises a
    CalledProcessError when a malformed string is passed to it."""
    malformed_string: str = "qwerty"
    img = None
    with pytest.raises(CalledProcessError):
        Image.build_from_string(".", "test", malformed_string)
    assert img is None


def test_run_interactive(test_image_id):
    """Tests that the run method correctly performs a simple action on a docker
    container when called."""
    img: Image = Image(test_image_id)

    retval = img.run('echo "Hello, World!"', interactive=True)
    assert retval == "Hello, World!\n"

    run(split("docker image remove test"))


def test_run_noninteractive(test_image_id):
    """Tests that the run method correctly performs a simple action on a docker
    container when called."""
    img: Image = Image(test_image_id)

    retval = img.run('echo "Hello, World!"', interactive=False)
    assert retval == "Hello, World!\n"

    run(split("docker image remove test"))


def test_run_interactive_print_to_file(test_image_id):
    """Tests that the run method correctly performs a simple action on a docker
    container when called."""
    img: Image = Image(test_image_id)

    file = open("testfile.txt", "w")

    retval = img.run(
        'echo "Hello, World!"',
        interactive=True,
        output_file=file)
    assert retval == "Hello, World!\n"

    file.close()
    file = open("testfile.txt", "r")
    file_txt = file.read()

    assert file_txt == retval

    file.close()

    run(split("docker image remove test"))


def test_run_interactive_malformed_command_exception(test_image_id):
    """Tests that the run method correctly raises a CalledProcessError when
    given a malformed command."""
    img: Image = Image(test_image_id)

    with pytest.raises(CalledProcessError):
        img.run("malformedcommand", interactive=True)

    run(split("docker image remove test"))


def test_tags(test_image_id):
    """Tests that an Image.tag call returns the same .RepoTags value as a
    typical docker inspect call."""
    img: Image = Image(test_image_id)

    inspect_process = run(
        split("docker inspect -f='{{.RepoTags}}' test"),
        capture_output=True,
        text=True,
        check=True,
    )
    tags = inspect_process.stdout.strip('][\n').split(', ')

    assert img.tags == tags
    run(split("docker image remove test"))


def test_id(test_image_id):
    """Tests that an Image.id call correctly returns the same ID value as given
    by a docker inspect call."""
    img = Image(test_image_id)

    inspect_process = run(
        split("docker inspect -f='{{.Id}}' test"),
        capture_output=True,
        text=True,
        check=True,
    )
    id = inspect_process.stdout.strip()

    assert img.id == id

    run(split("docker image remove test"))


def test_check_command_availability(test_image_id):
    """Tests that a check_command_availability properly returns the set of
    commands that exist on a given docker image and doesn't return commands
    that don't exist on that image.
    """
    check_me = [
        "apk", "apt-get", "yum", "curl", "wget", "python", "sh", "bash"
    ]
    check_me_2 = ["apt-get"]

    img = Image(test_image_id)
    retvals_1 = img.check_command_availability(check_me)
    run(split("docker image remove test"))

    run(split(
        "docker build . --file=./dockerfiles/alpine_functional " +
        "-t test_2")
        )
    img = Image("test_2")
    retvals_2 = img.check_command_availability(check_me)
    retvals_3 = img.check_command_availability(check_me_2)
    run(split("docker image remove test_2"))

    assert retvals_1 == ['apt-get', 'sh', 'bash']
    assert retvals_2 == ['apk', 'wget', 'sh', 'bash']
    assert not retvals_3


def test_check_command_availability_no_bash_exception():
    """Tests that a check_command_availability throws the
    CommandNotFoundOnImageError when called on an image that doesn't have
    bash installed.
    """
    check_me = [
        "apk"
    ]

    run(split(
        "docker build ./ --file=./dockerfiles/alpine_broken " +
        "-t test")
        )
    img = Image("test")
    with pytest.raises(CommandNotFoundOnImageError):
        img.check_command_availability(check_me)

    run(split("docker image remove test"))


def test_repr(test_image_id):
    """Tests that the __repr__() method of the Image class correctly produces
    representation strings"""
    id = test_image_id

    inspect_process = run(
        split("docker inspect -f='{{.RepoTags}}' test"),
        capture_output=True,
        text=True,
        check=True,
    )
    tags = inspect_process.stdout.strip('][\n').split(", ")

    img = Image(id)
    representation = repr(img)
    assert representation == f"Image(id={id}, tags={tags})"

    run(split("docker image remove test"))


def test_eq(test_image_id):
    """Tests that the __eq__() method of the Image class correctly compares
    Images with other Images and strings"""
    img = Image(test_image_id)

    img_2 = Image("test")

    assert img == img_2

    run(split("docker image remove test"))


def test_neq(test_image_id):
    """Tests that the internal __ne__() method of the Image class correctly
    compares Images with other nonequal Images and strings"""
    img = Image(test_image_id)

    img_2 = Image.build_from_dockerfile(
        ".",
        "b",
        dockerfile_loc="./dockerfiles/alpine_functional")

    assert img != "String"
    assert img != 0
    assert img != img_2

    run(split("docker image remove test"))
    run(split("docker image remove b"))


def test_get_image_id(test_image_id):
    """Tests that the get_image_id method returns the correct ID when given a
    properly-formed ID or docker image name."""
    id = test_image_id

    id_test = get_image_id("test")
    assert id_test == id

    id_test_2 = get_image_id(id)
    assert id_test_2 == id

    run(split("docker image remove test"))


def test_get_image_id_malformed_id_or_name():
    """Tests that the get_image_id method correctly raises a CalledProcessError
    when given a malformed name or ID."""
    with pytest.raises(CalledProcessError):
        get_image_id("malformed_name")
