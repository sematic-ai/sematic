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


def test_bool():
    with pytest.raises(NotImplementedError, match="docs.sematic.ai"):
        if foo():
            pass


def test_not():
    with pytest.raises(NotImplementedError, match="docs.sematic.ai"):
        if not foo():
            pass


def test_add():
    with pytest.raises(NotImplementedError, match="docs.sematic.ai"):
        foo() + 1


def test_iadd():
    with pytest.raises(NotImplementedError, match="docs.sematic.ai"):
        f = foo()
        f += 1


def test_mul():
    with pytest.raises(NotImplementedError, match="docs.sematic.ai"):
        foo() * 1


def test_imul():
    with pytest.raises(NotImplementedError, match="docs.sematic.ai"):
        f = foo()
        f *= 1


def test_div():
    with pytest.raises(NotImplementedError, match="docs.sematic.ai"):
        foo() / 1


def test_idiv():
    with pytest.raises(NotImplementedError, match="docs.sematic.ai"):
        f = foo()
        f /= 1
