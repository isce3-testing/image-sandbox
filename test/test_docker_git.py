from docker_cli._docker_git import git_extract_dockerfile
from docker_cli._url_reader import get_supported_url_readers, get_url_reader

from .utils import rough_dockerfile_validity_check


def test_git_dockerfile():
    """Performs a rough validity check of the Git dockerfile"""
    for supported_reader in get_supported_url_readers():
        url_reader = get_url_reader(supported_reader)
        dockerfile = git_extract_dockerfile(
            base="base",
            archive_url="www.url.com/a.tar.gz",
            folder_path="/",
            url_reader=url_reader,
        )
        rough_dockerfile_validity_check(dockerfile=dockerfile)
