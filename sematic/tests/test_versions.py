# Standard Library
import re

# Third-party
import yaml

# Sematic
from sematic.versions import (
    CURRENT_VERSION,
    MIN_CLIENT_SERVER_SUPPORTS,
    string_version_to_tuple,
    version_as_string,
)


CHANGELOG_MATCH_PATTERN = r"\* \[(\d+\.\d+\.\d+.*)\]\(.+\)$"
PYPI_BADGE_MATCH_PATTERN = (
    r"\!\[PyPI\]\(https://img.shields.io/pypi/v/sematic/"
    r"(\d+\.\d+\.\d+.*)\?style=for-the-badge\)$"
)


def test_min_client_version():
    assert MIN_CLIENT_SERVER_SUPPORTS <= CURRENT_VERSION


def test_changelog():
    changelog_version = None
    with open("docs/changelog.md", "r") as fp:
        for line in fp:
            # regex matches lines that start with a literal *, have a space, and then a
            # Markdown link containing MAJOR.MINOR.PATCH* where MAJOR, MINOR, and PATCH
            # consist only of digits (and at least one digit). It also allows for space
            # characters after the patch version before the end of the line.
            match = re.match(CHANGELOG_MATCH_PATTERN, line)
            if match is None:
                continue
            version_string = match.groups()[0]
            changelog_version = string_version_to_tuple(version_string)
            break

    assert (
        changelog_version is not None
    ), "Could not find a release version in 'changelog.md'."

    message = (
        f"Latest version in 'changelog.md' {changelog_version} doesn't "
        f"match the version in 'versions.py' {CURRENT_VERSION}."
    )
    assert changelog_version == CURRENT_VERSION, message


def test_helm_chart():
    with open("helm/sematic-server/Chart.yaml", "r") as fp:
        encodable = yaml.load(fp, yaml.Loader)

    image = encodable["appVersion"]
    prefix = "v"

    assert image.startswith(prefix), "Could not find a release version in 'Chart.yaml'."

    version_string = image.replace(prefix, "")
    values_version = string_version_to_tuple(version_string)
    message = (
        f"Latest version in 'Chart.yaml' {values_version} doesn't "
        f"match the version in 'versions.py' {CURRENT_VERSION}."
    )
    assert values_version == CURRENT_VERSION, message


def test_pyproject():
    with open("pyproject.toml", "r") as fp:
        matches = [re.match(r"version = \"([^\"]+)\"", line.strip()) for line in fp]

    matches = [match for match in matches if match is not None]
    assert len(matches) >= 1, "No version found in pyproject.toml"
    version_str = matches[0][1]
    pyproject_version = string_version_to_tuple(version_str)
    message = (
        f"Latest version in 'pyproject.toml' {pyproject_version} doesn't "
        f"match the version in 'versions.py' {CURRENT_VERSION}."
    )
    assert pyproject_version == CURRENT_VERSION, message


def test_pypi_badge():
    badge_version = None
    with open("README.md", "r") as fp:
        for line in fp:
            match = re.match(PYPI_BADGE_MATCH_PATTERN, line)
            if match is None:
                continue
            version_string = match.groups()[0]
            badge_version = string_version_to_tuple(version_string)
            break

    assert badge_version is not None, "Could not find a release version in 'README.md'."

    message = (
        f"Latest version in 'README.md' {badge_version} doesn't "
        f"match the version in 'versions.py' {CURRENT_VERSION}."
    )
    assert badge_version == CURRENT_VERSION, message


def test_string_version_to_tuple():
    as_string = "1.2.3"
    as_tuple = (1, 2, 3)
    assert version_as_string(as_tuple) == as_string
    assert string_version_to_tuple(as_string) == as_tuple


def test_exotic_string_version_to_tuple():
    as_string = "1.2.3+arch"
    as_tuple = (1, 2, 3)
    assert string_version_to_tuple(as_string) == as_tuple
