# Standard Library
import os
import re

# Third-party
import yaml

# Sematic
from sematic.versions import CURRENT_VERSION, MIN_CLIENT_SERVER_SUPPORTS


def test_min_client_version():
    assert MIN_CLIENT_SERVER_SUPPORTS <= CURRENT_VERSION


def test_changelog():
    changelog_version = None
    with open("docs/changelog.md", "r") as fp:
        for line in fp:
            # regex matches lines that start with a literal *, have a space,
            # and then MAJOR.MINOR.PATCH where MAJOR, MINOR, and PATCH consist
            # only of digits (and at least one digit). It also allows for space
            # characters after the patch version before the end of the line.
            match = re.match(r"\* \[(\d+\.\d+\.\d+.*)\]\(.+\)$", line)
            if match is None:
                continue
            version_string = match.groups()[0]
            changelog_version = tuple(int(v) for v in version_string.split("."))
            break

    message = (
        f"Latest version in changelog.md ({changelog_version}) doesn't "
        f"match the version in versions.py ({CURRENT_VERSION})."
    )
    assert changelog_version == CURRENT_VERSION, message


def test_helm_chart():
    with open("helm/sematic/values.yaml", "r") as fp:
        encodable = yaml.load(fp, yaml.Loader)

    image = encodable["server"]["image"]
    prefix = "sematicai/sematic-server:v"
    assert image.startswith(prefix)
    version_string = image.replace(prefix, "")
    values_version = tuple(int(v) for v in version_string.split("."))
    message = (
        f"Latest version in values.yaml ({version_string}) doesn't "
        f"match the version in versions.py ({CURRENT_VERSION})."
    )
    assert values_version == CURRENT_VERSION, message


def test_bazel_wheel_version():
    version_string = os.environ["BAZEL_WHEEL_VERSION"]
    bazel_wheel_version = tuple(int(v) for v in version_string.split("."))
    message = (
        f"Version in wheel_version.bzl ({bazel_wheel_version}) is inconsistent "
        f"with the version in versions.py ({CURRENT_VERSION})"
    )
    assert bazel_wheel_version == CURRENT_VERSION, message
