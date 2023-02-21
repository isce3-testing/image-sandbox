import os
from shlex import split
from subprocess import CalledProcessError, run

import pytest

from image import Image, get_image_id


def test_init():
    """Tests that the __init__ function on the Image class is correctly
    receiving and remembering the ID of a docker image."""
    run(split("docker build . -t test"))
    inspect_process = run(
        split("docker inspect -f='{{.Id}}' test"),
        capture_output=True,
        text=True,
        check=True,
    )
    id = inspect_process.stdout.strip()

    img = Image("test")

    assert img is not None
    assert img._id == id

    img_2 = Image(id)
    assert img_2._id == id

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
    assert img._id == id

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
    assert img._id == id
    assert os.stat("testfile.txt").st_size > 0

    run(split("docker image remove test"))


def test_build_from_dockerfile_dockerfile_in_different_location():
    """Tests that the build_from_dockerfile method can from a dockerfile in a
    different location than the context root directory."""
    img = Image.build_from_dockerfile(
        ".", "test", dockerfile_loc="test/Dockerfile"
    )
    inspect_process = run(
        split("docker inspect -f='{{.Id}}' test"),
        text=True,
        capture_output=True)
    id = inspect_process.stdout.strip()

    assert img is not None
    assert img._id == id
    run(split("docker image remove test"))


def test_build_from_dockerfile_context_in_different_location():
    """Tests that the build_from_dockerfile method can build when the context
    is set to a different directory."""
    img = Image.build_from_dockerfile(
        "./test", "test", dockerfile_loc="Dockerfile"
    )
    inspect_process = run(
        split("docker inspect -f='{{.Id}}' test"),
        text=True,
        capture_output=True)
    id = inspect_process.stdout.strip()

    assert img is not None
    assert img._id == id
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
    assert img._id == id
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
    assert img._id == id
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


def test_run_interactive():
    """Tests that the run method correctly performs a simple action on a docker
    container when called."""
    run(split("docker build . -t test"))
    img: Image = Image("test")

    retval = img.run('echo "Hello, World!"', interactive=True)
    assert retval == "Hello, World!\n"

    run(split("docker image remove test"))


def test_run_interactive_print_to_file():
    """Tests that the run method correctly performs a simple action on a docker
    container when called."""
    run(split("docker build . -t test"))
    img: Image = Image("test")

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


def test_run_interactive_malformed_command_exception():
    """Tests that the run method correctly raises a CalledProcessError when
    given a malformed command."""
    run(split("docker build . -t test"))
    img: Image = Image("test")

    with pytest.raises(CalledProcessError):
        img.run("malformedcommand", interactive=True)

    run(split("docker image remove test"))


def test_tags():
    """Tests that an Image.tag call returns the same .RepoTags value as a
    typical docker inspect call."""
    run(split("docker build . -t test"))
    inspect_process = run(
        split("docker inspect -f='{{.RepoTags}}' test"),
        capture_output=True,
        text=True,
        check=True,
    )
    tags = inspect_process.stdout.strip()

    img: Image = Image("test")
    assert img.tags == tags
    run(split("docker image remove test"))


def test_id():
    """Tests that an Image.id call correctly returns the same ID value as given
    by a docker inspect call."""
    run(split("docker build . -t test"))
    inspect_process = run(
        split("docker inspect -f='{{.Id}}' test"),
        capture_output=True,
        text=True,
        check=True,
    )
    id = inspect_process.stdout.strip()

    img = Image("test")
    assert img.id == id

    run(split("docker image remove test"))


def test_repr():
    """Tests that the __repr__() method of the Image class correctly produces
    representation strings"""
    run(split("docker build . -t test"))
    inspect_process = run(
        split("docker inspect -f='{{.Id}}' test"),
        capture_output=True,
        text=True,
        check=True,
    )
    id = inspect_process.stdout.strip()

    inspect_process = run(
        split("docker inspect -f='{{.RepoTags}}' test"),
        capture_output=True,
        text=True,
        check=True,
    )
    tags = inspect_process.stdout.strip()

    img = Image(id)
    representation = repr(img)
    assert representation == f"Image(id={id}, tags={tags})"

    run(split("docker image remove test"))


def test_eq():
    """Tests that the __eq__() method of the Image class correctly compares
    Images with other Images and strings"""
    img = Image.build_from_dockerfile(".", "test")
    inspect_process = run(
        split("docker inspect -f='{{.Id}}' test"),
        text=True,
        capture_output=True)
    id = inspect_process.stdout.strip()

    img_2 = Image(id)

    assert img == img_2

    run(split("docker image remove test"))


def test_neq():
    """Tests that the internal __ne__() method of the Image class correctly
    compares Images with other nonequal Images and strings"""
    img = Image.build_from_dockerfile(".", "a")

    img_2 = Image.build_from_dockerfile("./test", "b")

    assert img != "String"
    assert img != 0
    assert img != img_2

    run(split("docker image remove a"))
    run(split("docker image remove b"))


def test_get_image_id():
    """Tests that the get_image_id method returns the correct ID when given a
    properly-formed ID or docker image name."""
    run(split("docker build . -t test"))
    inspect_process = run(
        split("docker inspect -f='{{.Id}}' test"),
        capture_output=True,
        text=True,
        check=True,
    )
    id = inspect_process.stdout.strip()

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
