import random
from string import ascii_lowercase, digits


def generate_random_string(k: int = 10) -> str:
    """
    Generates a random lowercase alphanumeric string.

    Used to give unique names to Docker images - allows for multiple images of the same
    name to co-exist with different codes. Useful for testing and parallelism.

    Parameters
    ----------
    k : int, optional
        The number of characters in the string. Defaults to 10.

    Returns
    -------
    str
        The string.
    """
    return "".join(random.choices(ascii_lowercase + digits, k=k))
