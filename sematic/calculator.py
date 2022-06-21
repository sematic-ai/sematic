# Standard library
import inspect
import types
from typing import Any, Callable, Dict, Iterable, Union

# Sematic
from sematic.abstract_calculator import AbstractCalculator
from sematic.future import Future
from sematic.types.casting import safe_cast, can_cast_type
from sematic.types.type import is_type


class Calculator(AbstractCalculator):
    """
    A Calculator is Sematic's base unit of computation in a graph.

    Functions decorated with the `@calculator` decorator become
    instances of `Calculator`.
    """

    def __init__(
        self, func: types.FunctionType, input_types: Dict[str, type], output_type: type
    ) -> None:
        if not inspect.isfunction(func):
            raise ValueError("{} is not a function".format(func))

        self._func = func

        self._input_types = input_types
        self._output_type = output_type

        self.__doc__ = func.__doc__
        self.__module__ = func.__module__
        self.__name__ = func.__name__

    def __repr__(self):
        return "{}.{}".format(self.__module__, self.__name__)

    def get_source(self) -> str:
        try:
            return inspect.getsource(self._func)
        except OSError:
            return "# Source code not available"

    @property
    def func(self) -> types.FunctionType:
        return self._func

    @property
    def output_type(self) -> type:
        return self._output_type

    @property
    def input_types(self) -> Dict[str, type]:
        return self._input_types

    # Returns typing.Any instead of Future to ensure
    # calculator algebra is valid from a mypy perspective
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        signature = self.__signature__()
        argument_binding = signature.bind(*args, **kwargs)
        argument_map = argument_binding.arguments

        for name, parameter in signature.parameters.items():
            if name not in argument_map:
                argument_map[name] = parameter.default

        cast_arguments = self.cast_inputs(argument_map)

        return Future(self, cast_arguments)

    def __signature__(self) -> inspect.Signature:
        return inspect.signature(self._func)

    def calculate(self, **kwargs) -> Any:
        return self.func(**kwargs)

    def cast_inputs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempts to cast passed inputs to actual input values based on the
        calculator's input type signature.

        Parameters
        ----------
        kwargs: typing.Dict[str, typing.Any]
            Passed input values

        Returns
        -------
        typing.Dict[str, typing.Any]
            cast inputs
        """
        return {
            name: self.cast_value(
                kwargs[name],
                type_,
                error_prefix=(
                    "Invalid input type for argument {} when calling '{}'."
                ).format(repr(name), self),
            )
            for name, type_ in self.input_types.items()
        }

    def cast_output(self, value: Any) -> Any:
        """
        Attempts to cast the value returned by the calculator logic to an actual
        output value based on the calculator's output type signature.

        Parameters
        ----------
        value: typing.Any
            The output value of the calculator logic

        Returns
        -------
        typing.Any
            The cast output value
        """
        return self.cast_value(
            value,
            self.output_type,
            error_prefix="Invalid output type for '{}'.".format(self),
        )

    @staticmethod
    def cast_value(value: Any, type_: type, error_prefix: str = "") -> Any:
        """
        Attempts to cast a value to the passed type.
        """
        if isinstance(value, Future):
            can_cast, error = can_cast_type(value.calculator.output_type, type_)
            if not can_cast:
                raise TypeError(
                    "{} Cannot cast {} to {}: {}".format(
                        error_prefix, value.calculator.output_type, type_, error
                    )
                )
            return value

        if is_type(type(value)) and can_cast_type(type_, type(value))[0]:
            return value

        cast_value, error = safe_cast(value, type_)
        if error is not None:
            raise TypeError(
                "{} Cannot cast {} to {}: {}".format(error_prefix, value, type_, error)
            )

        return cast_value


def _repr_str_iterable(str_iterable: Iterable[str]) -> str:
    return ", ".join(repr(arg) for arg in sorted(str_iterable))


def calculator(
    func: Callable = None,
) -> Union[Callable, Calculator]:
    """
    calculator decorator.
    """

    def _wrapper(func_):

        annotations = func_.__annotations__

        output_type: type = type(None)
        input_types: Dict[str, type] = {}

        for name, type_ in annotations.items():
            if type_ is None:
                type_ = type(None)

            if name == "return":
                output_type = type_
            else:
                input_types[name] = type_

        full_arg_spec = _getfullargspec(func_)
        missing_annotations = set(full_arg_spec.args) - set(input_types)
        if len(missing_annotations) > 0:
            raise ValueError(
                (
                    "Missing calculator type annotations."
                    " The following arguments are not annotated: {}"
                ).format(_repr_str_iterable(missing_annotations))
            )

        return Calculator(func_, input_types=input_types, output_type=output_type)

    if func is None:
        return _wrapper

    return _wrapper(func)


def _getfullargspec(func_: Callable) -> inspect.FullArgSpec:
    """
    Validates the function's argument specification.

    Current validations:
    - The function has no variadic arguments (*args, **kwargs)
    """
    full_arg_spec = inspect.getfullargspec(func_)

    for arg in (full_arg_spec.varargs, full_arg_spec.varkw):
        if arg is not None:
            raise ValueError(
                (
                    "Variadic arguments are not supported."
                    " {} has variadic argument {}."
                    " See https://docs."
                ).format(func_, repr(arg))
            )

    return full_arg_spec
