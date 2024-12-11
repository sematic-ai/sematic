# Sematic
from sematic.utils.exceptions import ExceptionMetadata


class ParentError(Exception):
    pass


class Child1Error(ParentError):
    pass


class Child2Error(ParentError):
    pass


# for testing Diamond inheritance.
class GrandChildError(Child1Error, Child2Error):
    pass


def test_exception_metadata_from_exception():
    metadata = ExceptionMetadata.from_exception(ValueError("Hi there"))
    assert metadata.module == "builtins"
    assert metadata.name == "ValueError"
    assert metadata.repr == "Hi there"
    assert metadata.ancestors == ["builtins.Exception"]


def test_ancestors_from_exception():
    ancestors = ExceptionMetadata.ancestors_from_exception(Child1Error)
    ancestors = sorted(ancestors)
    assert ancestors == [
        "builtins.Exception",
        f"{ParentError.__module__}.ParentError",
    ]

    ancestors = ExceptionMetadata.ancestors_from_exception(GrandChildError)
    ancestors = sorted(ancestors)
    assert ancestors == [
        "builtins.Exception",
        f"{Child1Error.__module__}.Child1Error",
        f"{Child2Error.__module__}.Child2Error",
        f"{ParentError.__module__}.ParentError",
    ]

    ancestors = ExceptionMetadata.ancestors_from_exception(Child1Error("hi"))
    ancestors = sorted(ancestors)
    assert ancestors == [
        "builtins.Exception",
        f"{ParentError.__module__}.ParentError",
    ]


def test_is_instance_of():
    metadata = ExceptionMetadata.from_exception(Child1Error("Hi"))
    assert metadata.is_instance_of(Child1Error)
    assert metadata.is_instance_of(ParentError)
    assert metadata.is_instance_of(Exception)
    assert not metadata.is_instance_of(Child2Error)

    metadata = ExceptionMetadata.from_exception(GrandChildError("Hi"))
    assert metadata.is_instance_of(Child1Error)
    assert metadata.is_instance_of(Child2Error)
    assert metadata.is_instance_of(ParentError)
    assert metadata.is_instance_of(Exception)
    assert metadata.is_instance_of(GrandChildError)
