from shlex import split
from subprocess import run


def determine_scope(fixture_name, config) -> str:
    """
    Sets the scope of certain fixtures.

    Currently always returns "function." This is because bugs appear if different scopes
    are used. However, in the ideal case, parallel tests would have "function" scope
    while serial tests would have a wider scope like "session" to avoid re-creating
    identical docker images over and over.

    Parameters
    ----------
    fixture_name
        The name of the fixture.
    config
        A pytest internal object.

    Returns
    -------
    str
        The scope name.
    """
    # XXX: This uses "function" scope at all times but serial tests would theoretically
    # run faster if they had a wider scope. Presently this is necessary to prevent
    # errors but the whole system would be faster in serial if "session" was used.
    if hasattr(config.option, "numprocesses"):
        if config.option.numprocesses in ["auto", "logical"]:
            return "function"
    return "function"


def remove_docker_image(tag_or_id: str):
    """
    Idiot-proof removal of a docker image.

    Added because a missed word in a `docker image rm` command resulted in difficult
    debugging of a docker image being produced and not removed by the test suite.
    Best to ensure this is done the same way every time.

    Parameters
    ----------
    tag : str
        The tag or ID of the image.
    """
    run(split(f"docker image rm {tag_or_id}"))
