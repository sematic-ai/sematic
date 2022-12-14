# Standard Library
import logging
import sqlite3
import typing

logger = logging.getLogger(__name__)

# Represents the version of the client, server, and all other parts of
# the sdk. Should be bumped any time a release is made. Should be set
# to whatever is the version after the most recent one in changelog.md,
# as well as the version for the sematic wheel in wheel_version.bzl
CURRENT_VERSION = (0, 21, 0)

# Represents the smallest client version that works with the server
# at the CURRENT_VERSION. Should be updated any time a breaking change
# is made to the web API.
MIN_CLIENT_SERVER_SUPPORTS = (0, 19, 0)

# Support for dropping columns added in 3.35.0
MIN_SQLITE_VERSION = (3, 35, 0)


def _check_sqlite_version():
    version_tuple = sqlite3.sqlite_version.split(".")

    # get major/minor as ints. Patch can sometimes have non-digit chars
    major, minor = int(version_tuple[0]), int(version_tuple[1])
    if (major, minor) < MIN_SQLITE_VERSION:
        # TODO #302: implement sustainable way to upgrade sqlite3 DBs
        logger.warning(
            "Sematic will soon require the sqlite3 version to be at least %s, but your "
            "Python is using %s. Please upgrade. You may find this useful: "
            "https://stackoverflow.com/a/55729735/2540669",
            version_as_string(MIN_SQLITE_VERSION),
            sqlite3.sqlite_version,
        )


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
_check_sqlite_version()

if __name__ == "__main__":
    # It can be handy for deployment scripts and similar things to be able to get quick
    # access to the version. So make `python3 sematic/versions.py` print it out.
    print(CURRENT_VERSION_STR)
