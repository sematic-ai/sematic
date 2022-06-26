# Third-party
import pytest

# Sematic
from sematic.calculator import func


@func
def foo() -> str:
    return "foo"


def test_set():
    future = foo()
    f = future.set(name="some name", tags=["tag1", "tag2"])

    assert f.id == future.id
    assert f.name == "some name"
    assert f.tags == ["tag1", "tag2"]


def test_set_validate_name():
    future = foo()

    with pytest.raises(ValueError, match="Invalid name"):
        future.set(name=123)


def test_set_validate_tags():
    future = foo()

    with pytest.raises(ValueError, match="Invalid tags"):
        future.set(tags=123)


def test_set_validate_fields():
    future = foo()

    with pytest.raises(ValueError, match="Cannot mutate fields"):
        future.set(abc=123)


def test_no_tracking():
    assert foo().resolve(tracking=False) == "foo"


def test_getitem():
    with pytest.raises(NotImplementedError, match="docs.sematic.ai"):
        foo()[0]
