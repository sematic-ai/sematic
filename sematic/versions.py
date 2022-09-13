# Standard Library
import typing

# Represents the version of the client, server, and all other parts of
# the sdk. Should be bumped any time a release is made. Should be set
# to whatever is the version after the most recent one in changelog.md,
# as well as the version for the sematic wheel in wheel_version.bzl
CURRENT_VERSION = (0, 13, 0)

# Represents the smallest client version that works with the server
# at the CURRENT_VERSION. Should be updated any time a breaking change
# is made to the web API.
MIN_CLIENT_SERVER_SUPPORTS = (0, 11, 0)


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


CURRENT_VERSION_STR = version_as_string(CURRENT_VERSION)

if __name__ == "__main__":
    # It can be handy for deployment scripts and similar things to be able to get quick
    # access to the version. So make `python3 sematic/versions.py` print it out.
    print(CURRENT_VERSION_STR)
