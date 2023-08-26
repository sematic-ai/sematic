# Standard Library
import enum
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Type

# Third-party
import pytest

# Sematic
import sematic.api_client as api_client
from sematic.abstract_future import FutureState
from sematic.plugins.storage.memory_storage import MemoryStorage
from sematic.versions import CURRENT_VERSION, MIN_CLIENT_SERVER_SUPPORTS


@pytest.fixture(scope="function")
def test_storage():
    yield MemoryStorage


@pytest.fixture
def valid_client_version():
    current_version_metadata = api_client._server_version_metadata

    api_client._server_version_metadata = {
        "server": CURRENT_VERSION,
        "min_client_supported": MIN_CLIENT_SERVER_SUPPORTS,
    }

    try:
        yield
    finally:
        api_client._server_version_metadata = current_version_metadata


@pytest.fixture
def allow_any_run_state_transition():
    original = FutureState.is_allowed_transition
    try:
        FutureState.is_allowed_transition = lambda *args, **kwargs: True
        yield
    finally:
        FutureState.is_allowed_transition = original


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
