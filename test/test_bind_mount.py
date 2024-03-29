from pytest import raises

from wigwam._bind_mount import BindMount


def test_mount_init():
    """Tests that the mount object works and returns the correct string."""
    mount = BindMount(src="anything", dst="anything", permissions="ro")
    assert mount.mount_string() == "anything:anything:ro"


def test_mount_error():
    """
    Tests that the mount object fails to build when given an unrecognized
    permission.
    """
    with raises(ValueError):
        BindMount(
            src="anything",
            dst="anything",
            permissions="malformed",
        )
