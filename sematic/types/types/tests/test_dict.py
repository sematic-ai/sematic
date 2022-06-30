# Standard library
from typing import Dict, Union

# Third-party
import pytest

# Sematic
from sematic.types.casting import safe_cast
from sematic.types.serialization import get_json_encodable_summary


@pytest.mark.parametrize(
    "value, type_, expected_value, expected_error",
    (
        (dict(a=1), Dict[str, float], dict(a=1), None),
        (dict(a=1, b="foo"), Dict[str, Union[float, str]], dict(a=1, b="foo"), None),
        (dict(), Dict[str, float], dict(), None),
        (
            dict(a="foo"),
            Dict[str, int],
            None,
            "Cannot cast 'foo' to value type: Cannot cast 'foo' to <class 'int'>",
        ),
    ),
)
def test_dict(value, type_, expected_value, expected_error):
    cast_value, error = safe_cast(value, type_)

    assert error == expected_error
    assert cast_value == expected_value


def test_dict_summary():
    summary = get_json_encodable_summary(dict(a=123), Dict[str, int])

    assert summary == [("a", 123)]
