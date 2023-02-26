# Standard Library
import contextlib
import enum
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Type

# Third-party
import pytest

# Sematic
import sematic.api_client as api_client
import sematic.config.settings as sematic_settings
from sematic.plugins.storage.memory_storage import MemoryStorage


@pytest.fixture(scope="function")
def test_storage():
    yield MemoryStorage


@pytest.fixture
def valid_client_version():
    current_validated_client_version = api_client._validated_client_version

    api_client._validated_client_version = True

    try:
        yield
    finally:
        api_client._validated_client_version = current_validated_client_version


@contextlib.contextmanager
def environment_variables(to_set: Dict[str, Optional[str]]):
    """Context manager to configure the os environ for tests.

    Parameters
    ----------
    to_set:
        A dict from env var name to env var value. If the env var value
        is None, that will be treated as indicating that the env var should
        be unset within the managed context.
    """
    backup_of_changed_keys = {k: os.environ.get(k, None) for k in to_set.keys()}

    def update_environ_with(env_dict):
        # in case the specified variables are settings overrides, we need to
        # force reloading of global settings in order to apply the overrides
        sematic_settings._ACTIVE_SETTINGS = None

        for key, value in env_dict.items():
            if value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = value

    update_environ_with(to_set)
    try:
        yield
    finally:
        update_environ_with(backup_of_changed_keys)


class MyEnum(enum.Enum):
    A = "a"
    B = "b"


@dataclass
class MyDataclass:
    a: int
    b: str

    def __hash__(self):
        return self.a + len(self.b)


DIVERSE_VALUES_WITH_TYPES: List[Tuple[Optional[Any], Type[Any]]] = [
    (None, object),
    (None, Optional[int]),  # type: ignore
    (1, int),
    ("a", str),
    (MyEnum.A, type(MyEnum.A)),
    (MyDataclass(a=1, b="b"), MyDataclass),
    ([], List[object]),
    ([None], List[object]),
    ([None], List[Optional[int]]),
    ([1, 2, 3], List[int]),
    (["a", "b", "c"], List[str]),
    ([MyEnum.A, MyEnum.B], List[type(MyEnum.A)]),  # type: ignore
    ([MyDataclass(a=1, b="b"), MyDataclass(a=0, b="")], List[MyDataclass]),
    ([None, 1, "a", MyEnum.A, MyDataclass(a=1, b="b")], List[object]),
    (  # type: ignore
        (None, None, 1, "a", MyEnum.A, MyDataclass(a=1, b="b")),
        Tuple[object, Optional[int], int, str, type(MyEnum.A), MyDataclass],
    ),
    (dict(), Dict[int, int]),
    ({None: None}, Dict[object, object]),
    ({None: None}, Dict[Optional[int], Optional[int]]),
    ({"a": 1, "b": 2}, Dict[str, int]),
    ({1: "a", 2: "b"}, Dict[int, str]),
    (
        {MyEnum.A: MyEnum.A, MyEnum.B: MyEnum.B},
        Dict[type(MyEnum.A), type(MyEnum.A)],  # type: ignore
    ),
    (
        {MyDataclass(a=1, b="b"): MyDataclass(a=1, b="b")},
        Dict[MyDataclass, MyDataclass],
    ),
    (
        {
            None: None,
            1: 1,
            "a": "a",
            MyEnum.A: MyEnum.A,
            MyDataclass(a=1, b="b"): MyDataclass(a=1, b="b"),
        },
        Dict[object, object],
    ),
]
