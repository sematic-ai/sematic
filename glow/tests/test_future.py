# Glow
# Third-party
import pytest

# Glow
from glow.calculator import calculator


@calculator
def func():
    pass


def test_set():
    future = func()
    f = future.set(name="some name", tags=["tag1", "tag2"])

    assert f.id == future.id
    assert f.name == "some name"
    assert f.tags == ["tag1", "tag2"]


def test_set_validate_name():
    future = func()

    with pytest.raises(ValueError, match="Invalid name"):
        future.set(name=123)


def test_set_validate_tags():
    future = func()

    with pytest.raises(ValueError, match="Invalid tags"):
        future.set(tags=123)


def test_set_validate_fields():
    future = func()

    with pytest.raises(ValueError, match="Cannot mutate fields"):
        future.set(abc=123)
