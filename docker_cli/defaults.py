from pathlib import Path


def universal_tag_prefix() -> str:
    """Returns a prefix for tags generated by the system."""
    return "dcli"


def install_prefix() -> Path:
    """Returns the build system's default install prefix path."""
    return Path("/app")


def build_prefix() -> Path:
    """Returns the build system's default build prefix path."""
    return Path("/tmp/build")