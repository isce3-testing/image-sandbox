from pathlib import Path
from shlex import split
from subprocess import PIPE, CalledProcessError, run
from tempfile import NamedTemporaryFile

import pytest

from docker_cli import CommandNotFoundError, DockerBuildError, Image
from docker_cli._exceptions import ImageNotFoundError
from docker_cli._image import get_image_id


def test_init(image_id):
    """
    Tests that the __init__ function on the Image class is correctly
    receiving and remembering the ID of a docker image.
    """
    id = image_id
    print("ID: " + id)
    img = Image("test")

    assert img is not None
    assert img.id == id

    img_2 = Image(id)
    assert img_2.id == id


def test_bad_init():
    """
    Tests that the __init__ function on the Image class raises a
    CalledProcessError when given a malformed name.
    """
    img = None
    with pytest.raises(ImageNotFoundError):
        img = Image("malformed_image_name_or_id")
    assert img is None


def test_build_from_dockerfile():
    """
    Tests that the build method constructs and returns an Image when
    given a Dockerfile.
    """
    try:
        img = Image.build(tag="test", dockerfile="")
        inspect_process = run(
            split("docker inspect -f='{{.Id}}' test"),
            text=True,
            capture_output=True)
        id = inspect_process.stdout.strip()

        assert img is not None
        assert img.id == id
    finally:
        run(split("docker image rm test"))


def test_build_from_dockerfile_output_to_file():
    """
    Tests that the build method writes to a file when configured to
    do so.
    """
    tmp = NamedTemporaryFile()
    try:
        with open(tmp.name, "w") as file:
            img = Image.build(
                tag="test",
                dockerfile="",
                stdout=file,
                stderr=file
            )
        with open(tmp.name) as file:
            assert len(file.read()) > 0

        inspect_process = run(
            split("docker inspect -f='{{.Id}}' test"),
            text=True,
            capture_output=True)
        id = inspect_process.stdout.strip()

        assert img is not None
        assert img.id == id
    finally:
        run(split("docker image rm test"))


def test_build_from_dockerfile_dockerfile_in_different_location():
    """
    Tests that the build method can build an image from a dockerfile in a
    different location than the context root directory.
    """
    try:
        img = Image.build(
            tag="test", dockerfile="dockerfiles/alpine_functional.dockerfile"
        )
        inspect_process = run(
            split("docker inspect -f='{{.Id}}' test"),
            text=True,
            capture_output=True)
        id = inspect_process.stdout.strip()

        assert img is not None
        assert img.id == id
    finally:
        run(split("docker image rm test"))


def test_build_from_dockerfile_context_in_different_location():
    """
    Tests that the build method can build when the context is set to a
    different directory.
    """
    try:
        img = Image.build(
            context="dockerfiles",
            tag="test",
            dockerfile="dockerfiles/alpine_functional.dockerfile"
        )
        inspect_process = run(
            split("docker inspect -f='{{.Id}}' test"),
            text=True,
            capture_output=True)
        id = inspect_process.stdout.strip()

        assert img is not None
        assert img.id == id
    finally:
        run(split("docker image rm test"))


def test_build_from_dockerfile_in_malformed_location():
    """
    Tests that the build method raises a DockerBuildError when a malformed
    dockerfile location is given.
    """
    img = None
    with pytest.raises(DockerBuildError):
        img = Image.build(
            tag="test",
            dockerfile="non_existent_directory/Dockerfile")
    assert img is None


def test_build_from_string():
    """Tests that the build method builds and returns an Image when given a
    dockerfile-formatted string."""
    dockerfile = Path("dockerfile").read_text()
    try:
        img: Image = Image.build(
            tag="test",
            dockerfile_string=dockerfile)
        inspect_process = run(
            split("docker inspect -f='{{.Id}}' test"),
            text=True,
            capture_output=True)
        id = inspect_process.stdout.strip()

        assert img is not None
        assert img.id == id
    finally:
        run(split("docker image rm test"))


def test_build_from_string_output_to_file():
    """
    Tests that the build method writes to a file when formatted to do so and
    given a dockerfile string.
    """
    tmp = NamedTemporaryFile()
    dockerfile: str = Path("dockerfile").read_text()
    try:
        with open(tmp.name, "w") as file:
            img: Image = Image.build(
                tag="test",
                dockerfile_string=dockerfile,
                stdout=file,
                stderr=file)
        with open(tmp.name) as file:
            assert len(file.read()) > 0
        inspect_process = run(
            split("docker inspect -f='{{.Id}}' test"),
            text=True,
            capture_output=True)
        id = inspect_process.stdout.strip()

        assert img is not None
        assert img.id == id
    finally:
        run(split("docker image rm test"))


def test_build_from_malformed_string():
    """
    Tests that the build method raises a DockerBuildError when a malformed
    dockerfile string is passed to it.
    """
    malformed_string: str = "qwerty"
    img = None
    with pytest.raises(DockerBuildError):
        Image.build(
            tag="test",
            dockerfile_string=malformed_string
        )
    assert img is None


def test_run_interactive(image_id):
    """
    Tests that the run method performs a simple action on a docker container
    when called with interactive = True.
    """
    img: Image = Image(image_id)

    retval = img.run(
        'echo "Hello, World!"',
        interactive=True,
        stdout=PIPE
    )
    assert "Hello, World!\n" in retval


def test_run_noninteractive(image_id):
    """
    Tests that the run method performs a simple action on a docker container
    when called with interactive = False.
    """
    img: Image = Image(image_id)

    retval = img.run(
        'echo "Hello, World!"',
        interactive=False,
        stdout=PIPE
    )
    assert "Hello, World!\n" in retval


def test_run_noninteractive_output_redirect(image_id):
    """
    Tests that the run method returns only the value of stdout when the
    value of stderr is written to None and stdout is written to PIPE.
    """
    img: Image = Image(image_id)

    retval = img.run(
        'echo "Hello, World!"',
        interactive=True,
        stdout=PIPE,
        stderr=None
    )
    assert retval == "Hello, World!\n"


def test_run_interactive_print_to_file(image_id):
    """
    Tests that the run method prints to a file when interactive = True.
    """
    img: Image = Image(image_id)
    tmp = NamedTemporaryFile()
    with open(tmp.name, "w") as file:

        img.run(
            'echo "Hello, World!"',
            interactive=True,
            stdout=file,
            stderr=file
        )
    with open(tmp.name) as file:
        file_txt = file.read()
        print(file_txt)

    assert "Hello, World!\n" in file_txt


def test_run_interactive_malformed_command_exception(image_id):
    """
    Tests that the run method raises a CalledProcessError when given a
    malformed command.
    """
    img: Image = Image(image_id)

    with pytest.raises(CalledProcessError):
        img.run("malformedcommand", interactive=True)


def test_tags(image_id):
    """
    Tests that an Image.tag call returns the same .RepoTags value as a
    typical docker inspect call.
    """
    img: Image = Image(image_id)

    inspect_process = run(
        split("docker inspect -f='{{.RepoTags}}' test"),
        capture_output=True,
        text=True,
        check=True,
    )
    tags = inspect_process.stdout.strip('][\n').split(', ')

    assert img.tags == tags


def test_id(image_id):
    """
    Tests that an Image.id call returns the same ID value as given by a docker
    inspect call.
    """
    img = Image(image_id)

    inspect_process = run(
        split("docker inspect -f='{{.Id}}' test"),
        capture_output=True,
        text=True,
        check=True,
    )
    id = inspect_process.stdout.strip()

    assert img.id == id


def test_check_command_availability(image_id, ):
    """
    Tests that a check_command_availability properly returns the set of
    commands that exist on an Image and not ones that don't.
    """
    check_me = [
        "apk", "apt-get", "yum", "curl", "wget", "python", "sh", "bash"
    ]
    check_me_2 = ["apt-get"]

    img = Image(image_id)
    retvals_1 = img.check_command_availability(check_me)

    try:
        run(split(
            "docker build . --file=dockerfiles/alpine_functional.dockerfile -t test_2")
            )
        img = Image("test_2")
        retvals_2 = img.check_command_availability(check_me)
        retvals_3 = img.check_command_availability(check_me_2)
        run(split("docker image remove test_2"))

        assert retvals_1 == ['apt-get', 'sh', 'bash']
        assert retvals_2 == ['apk', 'wget', 'sh', 'bash']
        assert len(retvals_3) == 0
    finally:
        run(split("docker image rm test"))


def test_check_command_availability_no_bash_exception():
    """
    Validates that a check_command_availability throws the
    CommandNotFoundOnImageError when called on an image that doesn't have
    bash installed.
    """
    check_me = [
        "apk"
    ]
    try:
        run(split(
            "docker build ./ --file=dockerfiles/alpine_broken.dockerfile -t test")
            )
        img = Image("test")
        with pytest.raises(CommandNotFoundError):
            img.check_command_availability(check_me)
    finally:
        run(split("docker image rm test"))


def test_repr(image_id):
    """
    Tests that the __repr__() method of the Image class correctly produces
    representation strings.
    """
    id = image_id

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


def test_eq(image_id):
    """
    Tests that the __eq__() method of the Image class correctly compares
    Images with other Images.
    """
    img = Image(image_id)

    img_2 = Image("test")

    assert img == img_2


def test_neq(image_id, ):
    """
    Tests that the internal __ne__() method of the Image class correctly
    compares Images with other nonequal Images and objects.
    """
    img = Image(image_id)
    try:
        img_2 = Image.build(
            tag="b",
            dockerfile="dockerfiles/alpine_functional.dockerfile"
        )

        assert img != "String"
        assert img != 0
        assert img != img_2
    finally:
        run(split("docker image remove b"))


def test_get_image_id(image_id):
    """
    Tests that the get_image_id method returns the correct ID when given a
    properly-formed ID or docker image name.
    """
    id = image_id

    id_test = get_image_id("test")
    assert id_test == id

    id_test_2 = get_image_id(id)
    assert id_test_2 == id


def test_get_image_id_malformed_id_or_name():
    """
    Validates that the get_image_id method raises a CalledProcessError when
    given a malformed name or ID.
    """
    with pytest.raises(ImageNotFoundError):
        get_image_id("malformed_name")
