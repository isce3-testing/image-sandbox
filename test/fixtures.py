"""This file contains all fixtures that are needed by multiple test files."""
from shlex import split
from subprocess import run
from textwrap import dedent

from pytest import fixture

from docker_cli.utils import generate_codename

from .utils import determine_scope, remove_docker_image


@fixture(scope=determine_scope)
def image_tag():
    """
    Returns an image tag

    Returns
    ------
    str
        An image tag
    """
    tag = f"isce3_pytest_temp_{generate_codename(k=10)}"
    yield tag


@fixture(scope="function")
def image_id(image_tag):
    """
    Builds an image for testing and returns its ID.

    Yields
    ------
    str
        An image ID.
    """
    dockerfile = dedent(f"""\
        FROM ubuntu

        RUN echo {image_tag}
    """.rstrip())
    run(split(f"docker build . -t {image_tag} -f-"), text=True, input=dockerfile)
    inspect_process = run(
        split("docker inspect -f='{{.Id}}' " + image_tag),
        capture_output=True,
        text=True,
        check=True,
    )
    id = inspect_process.stdout.strip()
    yield id
    remove_docker_image(image_tag)
