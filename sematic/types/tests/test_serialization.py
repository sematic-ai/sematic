# Standard Library
from dataclasses import dataclass
from typing import Union

# Sematic
from sematic.types.serialization import _is_dataclass


@dataclass
class Dc:
    field: int


class DcChild(Dc):
    pass


@dataclass
class DcDcChild(Dc):
    field2: int


class Plain:
    pass


def test_is_dataclass():
    assert _is_dataclass(Dc)
    assert not _is_dataclass(DcChild)
    assert not _is_dataclass(Plain)
    assert _is_dataclass(DcDcChild)
    assert not _is_dataclass(Union[Dc, Plain])
    assert not _is_dataclass(Union)
