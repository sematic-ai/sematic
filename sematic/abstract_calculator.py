"""
Module defining AbstractCalculator.

This is needed to avoid circular dependencies between
modules for Calculator and Future.
"""
# Standard Library
import abc
import typing


class CalculatorError(Exception):
    """Error when the exception originated inside user code"""

    pass


class AbstractCalculator(abc.ABC):
    def __init__(self) -> None:
        # Simply typing attributes
        self.__name__: str

    @abc.abstractmethod
    def calculate(self, **kwargs) -> typing.Any:
        pass

    @abc.abstractmethod
    def cast_inputs(
        self, kwargs: typing.Dict[str, typing.Any]
    ) -> typing.Dict[str, typing.Any]:
        pass

    @abc.abstractmethod
    def cast_output(self, value: typing.Any) -> typing.Any:
        pass

    @abc.abstractproperty
    def input_types(self) -> typing.Dict[str, type]:
        pass

    @abc.abstractproperty
    def output_type(self) -> type:
        pass

    @abc.abstractmethod
    def get_source(self) -> str:
        pass
