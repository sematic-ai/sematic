# Standard Library
import os
import re

# Sematic
from sematic.versions import CURRENT_VERSION, MIN_CLIENT_SERVER_SUPPORTS


def test_min_client_version():
    assert MIN_CLIENT_SERVER_SUPPORTS <= CURRENT_VERSION


def test_changelog():
    changelog_versions = []
    with open("docs/changelog.md", "r") as fp:
        for line in fp:
            # regex matches lines that start with a literal *, have a space,
            # and then MAJOR.MINOR.PATCH where MAJOR, MINOR, and PATCH consist
            # only of digits (and at least one digit). It also allows for space
            # characters after the patch version before the end of the line.
            if re.match(r"\* \d+\.\d+.\d+\s*$", line) is None:
                continue
            version_string = line[len("* ") :]  # noqa: E203
            changelog_versions.append(tuple(int(v) for v in version_string.split(".")))

    message = (
        f"Latest version in changelog.md ({changelog_versions[0]}) doesn't "
        f"match the version in versions.py ({CURRENT_VERSION})."
    )
    assert changelog_versions[0] == CURRENT_VERSION, message

    # assert versions are in descending order
    for version, following_version in zip(changelog_versions, changelog_versions[1:]):
        assert version > following_version


def test_bazel_wheel_version():
    version_string = os.environ["BAZEL_WHEEL_VERSION"]
    bazel_wheel_version = tuple(int(v) for v in version_string.split("."))
    message = (
        f"Version in wheel_version.bzl ({bazel_wheel_version}) is inconsistent "
        f"with the version in versions.py ({CURRENT_VERSION})"
    )
    assert bazel_wheel_version == CURRENT_VERSION, message
