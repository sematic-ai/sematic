# Standard Library
import time

# Third-party
import pytest

# Sematic
from sematic.utils.exceptions import TimeoutError
from sematic.utils.timeout import timeout


def do_lengthy(duration_seconds):
    started = time.time()
    while time.time() - started < duration_seconds:
        time.sleep(0.01)


def test_timeout():
    # do a non-expiration followed by an
    # expiration and another non-expiration.
    # Why all these in one test? Because we
    # also want to test that the timeout code is
    # cleaning up properly between usages.
    with timeout(duration_seconds=10):
        do_lengthy(0.2)

    with pytest.raises(TimeoutError):
        with timeout(duration_seconds=1):
            do_lengthy(10)

    with timeout(duration_seconds=10):
        do_lengthy(0.2)


def test_none_timeout():
    with timeout(None):
        do_lengthy(0.2)


def test_bad_arg_timeout():
    with pytest.raises(ValueError):
        with timeout(0.5):
            do_lengthy(0.2)

    with pytest.raises(ValueError):
        with timeout(0):
            do_lengthy(0.2)

    with pytest.raises(ValueError):
        with timeout(-1):
            do_lengthy(0.2)
