# Standard Library
import logging
import typing

logger = logging.getLogger(__name__)

# Represents the version of the client, server, and all other parts of
# the sdk. Should be bumped any time a release is made. Should be set
# to whatever is the version after the most recent one in changelog.md,
# as well as the version for the sematic wheel in wheel_constants.bzl
CURRENT_VERSION = (0, 25, 0)

# Represents the smallest client version that works with the server
# at the CURRENT_VERSION. Should be updated any time a breaking change
# is made to the web API. If there is a breaking change, there should
# be a TODO below
MIN_CLIENT_SERVER_SUPPORTS = (0, 22, 1)

# Version of the settings file schema
SETTINGS_SCHEMA_VERSION = 1


def version_as_string(version: typing.Tuple[int, int, int]) -> str:
    """Given a version tuple, return its equivalent string.

    Parameters
    ----------
    version:
        A tuple with three integers representing a semantic version

    Returns
    -------
    A string formatted as <MAJOR>.<MINOR>.<PATCH>
    """
    return ".".join(str(v) for v in version)


def string_version_to_tuple(version_string: str) -> typing.Tuple[int, int, int]:
    """Given a version string, return its equivalent tuple.

    Parameters
    ----------
    version_string:
        A string formatted as <MAJOR>.<MINOR>.<PATCH>

    Returns
    -------
    A tuple with three integers representing a semantic version
    """
    string_components = version_string.split(".")
    if len(string_components) < 3:
        raise ValueError(
            f"Version strings should have at least three digits. Got: {version_string}"
        )
    return tuple(int(v) for v in string_components[:3])  # type: ignore


CURRENT_VERSION_STR = version_as_string(CURRENT_VERSION)
MIN_CLIENT_SERVER_SUPPORTS_STR = version_as_string(MIN_CLIENT_SERVER_SUPPORTS)


if __name__ == "__main__":
    # It can be handy for deployment scripts and similar things to be able to get quick
    # access to the version. So make `python3 sematic/versions.py` print it out.
    print(CURRENT_VERSION_STR)
