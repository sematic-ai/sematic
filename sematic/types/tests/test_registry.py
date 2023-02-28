# Standard Library
from abc import ABC, ABCMeta, abstractmethod
from dataclasses import dataclass
from enum import Enum, unique
from typing import Any, List, Literal, Optional, Union

# Third-party
import pytest

# Sematic
from sematic.types.registry import (
    _validate_registry_keys,
    is_parameterized_generic,
    is_supported_type_annotation,
    validate_type_annotation,
)


@unique
class Color(Enum):
    RED = "RED"
    GREEN = "GREEN"
    BLUE = "BLUE"


@dataclass
class FooDataclass:
    foo: int


class FooStandard:
    pass


class FooAbc(ABC):
    @abstractmethod
    def do_foo(self):
        pass


class FooAbcMeta(metaclass=ABCMeta):
    @abstractmethod
    def do_foo(self):
        pass


def test_validate_type_annotation():
    validate_type_annotation(int)
    validate_type_annotation(Color)
    validate_type_annotation(FooDataclass)
    validate_type_annotation(FooStandard)
    validate_type_annotation(FooAbc)
    validate_type_annotation(FooAbcMeta)
    validate_type_annotation(Union[int, float])
    validate_type_annotation(Optional[int])
    validate_type_annotation(List[int])
    validate_type_annotation(List[int], int)
    with pytest.raises(TypeError, match=r"Expected a Sematic-supported type here"):
        validate_type_annotation(42)
    with pytest.raises(TypeError, match=r"Expected a Sematic-supported type here"):
        validate_type_annotation(List[int], 42)
    with pytest.raises(TypeError, match=r"Expected a Sematic-supported type here"):
        validate_type_annotation(Literal[42])
    with pytest.raises(
        TypeError, match=r"'Any' is not a Sematic-supported.*'object' instead."
    ):
        validate_type_annotation(Any)
    with pytest.raises(TypeError, match=r"Union must be parametrized.*"):
        validate_type_annotation(Union)


def test_is_supported_type_annotation():
    assert is_supported_type_annotation(FooDataclass)
    assert is_supported_type_annotation(Color)
    assert is_supported_type_annotation(FooAbc)
    assert is_supported_type_annotation(FooAbcMeta)
    assert not is_supported_type_annotation(Union)


def test_is_parameterized_generic():
    assert not is_parameterized_generic(FooDataclass)
    assert not is_parameterized_generic(FooStandard)
    assert not is_parameterized_generic(Color)
    assert not is_parameterized_generic(FooAbc)
    assert not is_parameterized_generic(FooAbcMeta)
    assert is_parameterized_generic(Union[int, float])
    assert is_parameterized_generic(Optional[int])
    assert is_parameterized_generic(List[int])
    assert not is_parameterized_generic(Literal[42])
    assert not is_parameterized_generic(Any)
    assert not is_parameterized_generic(Union)


def test_validate_registry_keys():
    _validate_registry_keys(int)
    _validate_registry_keys(int, int)
    _validate_registry_keys(FooDataclass)
    _validate_registry_keys(FooStandard)
    _validate_registry_keys(FooAbc)
    _validate_registry_keys(FooAbcMeta)
    _validate_registry_keys(Color)
    _validate_registry_keys(Union)
    _validate_registry_keys(List)
    with pytest.raises(
        TypeError, match=r"Cannot register type typing.Union\[int, float\]"
    ):
        _validate_registry_keys(Union[int, float])
    with pytest.raises(TypeError, match=r"Cannot register type 42"):
        _validate_registry_keys(42)
