# Standard Library
from dataclasses import dataclass

# Third-party
import pytest

# Sematic
from sematic.future_context import (
    AbstractExternalResource,
    PrivateContext,
    SematicContext,
    context,
    set_context,
)


@dataclass
class FakeExternalResource(AbstractExternalResource):
    x: int


def test_abstract_external_resource():
    with set_context(
        SematicContext(
            run_id="run_id",
            root_id="root_id",
            private=PrivateContext(
                resolver_class_path="a.b.c",
            ),
        )
    ):
        assert len(context().private.external_resources) == 0
        with FakeExternalResource(42) as r:
            assert r.x == 42
            assert len(context().private.external_resources) == 1
            assert r == context().private.external_resources[0]
        assert len(context().private.external_resources) == 0


def test_abstract_external_resource_multiple_resources():
    with set_context(
        SematicContext(
            run_id="run_id",
            root_id="root_id",
            private=PrivateContext(
                resolver_class_path="a.b.c",
            ),
        )
    ):
        assert len(context().private.external_resources) == 0
        with FakeExternalResource(42):
            with pytest.raises(
                RuntimeError,
                match=r".*only allows one 'with' block resource to be active at a time.*",
            ):
                with FakeExternalResource(43):
                    raise AssertionError(
                        "Should not make it into double resource block"
                    )
