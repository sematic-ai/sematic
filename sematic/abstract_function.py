"""
Module defining AbstractFunction.

This is needed to avoid circular dependencies between
modules for Function and Future.
"""

# Standard Library
import abc
import typing


class FunctionError(Exception):
    """Error when the exception originated inside user code"""

    pass


class AbstractFunction(abc.ABC):
    def __init__(self) -> None:
        # Simply typing attributes
        self.__name__: str

    @abc.abstractmethod
    def execute(self, **kwargs) -> typing.Any:
        pass

    @abc.abstractmethod
    def cast_inputs(
        self, kwargs: typing.Dict[str, typing.Any]
    ) -> typing.Dict[str, typing.Any]:
        pass

    @abc.abstractmethod
    def cast_output(self, value: typing.Any) -> typing.Any:
        pass

    @property
    @abc.abstractmethod
    def input_types(self) -> typing.Dict[str, type]:
        pass

    @property
    @abc.abstractmethod
    def output_type(self) -> type:
        pass

    @abc.abstractmethod
    def get_source(self) -> str:
        pass

    @abc.abstractmethod
    def __call__(self, **kwargs) -> typing.Any:
        pass
