from pytest import fixture, mark, raises

from docker_cli import DockerBuildError, Dockerfile

from .utils import determine_scope, remove_docker_image


@fixture(scope=determine_scope)
def testing_dockerfile() -> Dockerfile:
    """
    Returns a basic dockerfile.

    Returns
    -------
    Dockerfile
        The dockerfile.
    """
    return Dockerfile(
        header="# Header",
        body="RUN echo \"Hello, World!\""
    )


@mark.dockerfiles
class TestDockerfile:
    def test_init(self, testing_dockerfile):
        """Determines if the Fockerfile object constructs properly."""

        assert testing_dockerfile.body == "RUN echo \"Hello, World!\""
        assert testing_dockerfile.header == "# Header"

    def test_combine_dockerfiles(self):
        """Determines if dockerfile combining works."""

        dockerfile_1: Dockerfile = Dockerfile(
            body="# Prior",
            header="# Prior"
        )

        dockerfile_2: Dockerfile = Dockerfile(
            body="# After",
            header="# After"
        )

        test_dockerfile = Dockerfile.combine_dockerfiles(
            dockerfile_1=dockerfile_1,
            dockerfile_2=dockerfile_2
        )

        assert test_dockerfile.body == "# Prior\n# After"
        assert test_dockerfile.header == "# Prior\n# After"

    def test_full_dockerfile(self, testing_dockerfile: Dockerfile, image_tag):
        """Determines that the full dockerfile string returns properly."""

        docker_string = testing_dockerfile.full_dockerfile(parent=image_tag)

        expected_string: str = f"# Header\nFROM {image_tag}\n\n" \
            "RUN echo \"Hello, World!\""

        assert docker_string == expected_string

    def test_build(self, testing_dockerfile: Dockerfile, image_tag):
        """Determines if the build method works."""
        try:
            testing_dockerfile.build(base="ubuntu", tag=image_tag)
        finally:
            remove_docker_image(image_tag)

    def test_build_malformed_dockerfile(self, image_tag):
        """Determines if the Dockerfile.build method raises a DockerBuildError properly
        when given a malformed dockerfile."""
        malformed_dockerfile = Dockerfile(
            header="bare string",
            body="bare string"
        )
        with raises(DockerBuildError):
            malformed_dockerfile.build(tag=image_tag, base="ubuntu")

    def test_prepend_body(self, testing_dockerfile: Dockerfile):
        """Determines if the Dockerfile prepends text to the body properly."""
        initial_body = testing_dockerfile.body
        prepended_text = "# test"
        testing_dockerfile.prepend_body(prepended_text)

        assert testing_dockerfile.body == prepended_text + "\n" + initial_body

    def test_append_body(self, testing_dockerfile: Dockerfile):
        """Determines if the Dockerfile appends text to the body properly."""
        initial_body = testing_dockerfile.body
        appended_text = "# test"
        testing_dockerfile.append_body(appended_text)

        assert testing_dockerfile.body == initial_body + "\n" + appended_text

    def test_prepend_header(self, testing_dockerfile: Dockerfile):
        """Determines if the Dockerfile prepends text to the header properly."""
        initial_header = testing_dockerfile.header
        prepended_text = "# test"
        testing_dockerfile.prepend_header(prepended_text)

        assert testing_dockerfile.header == prepended_text + "\n" + initial_header

    def test_append_header(self, testing_dockerfile: Dockerfile):
        """Determines if the Dockerfile appends text to the body properly."""
        initial_header = testing_dockerfile.header
        appended_text = "# test"
        testing_dockerfile.append_header(appended_text)

        assert testing_dockerfile.header == initial_header + "\n" + appended_text

    def test_body(self):
        """Determines that the body property returns the body of the Dockerfile."""
        dockerfile = Dockerfile(body="# body")
        assert dockerfile.body == "# body"

    def test_body_setter(self, testing_dockerfile: Dockerfile):
        """Determines that the body setter sets the body of the Dockerfile."""
        testing_dockerfile.body = "# body"
        assert testing_dockerfile.body == "# body"

    def test_header(self, ):
        """Determines that the header property returns the header of the Dockerfile."""
        dockerfile = Dockerfile(body="", header="# header")
        assert dockerfile.header == "# header"

    def test_header_setter(self, testing_dockerfile: Dockerfile):
        """Determines that the header setter sets the header of the Dockerfile."""
        testing_dockerfile.header = "# header"
        assert testing_dockerfile.header == "# header"
