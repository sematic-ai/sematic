# Standard library
import collections
import inspect
import types
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
)

# Sematic
from sematic.abstract_calculator import AbstractCalculator
from sematic.future import Future
from sematic.resolvers.resource_requirements import ResourceRequirements
from sematic.types.casting import safe_cast, can_cast_type
from sematic.types.type import is_type
from sematic.types.registry import get_origin_type, is_valid_typing_alias


class Calculator(AbstractCalculator):
    """
    A Calculator is Sematic's base unit of computation in a graph.

    Functions decorated with the `@calculator` decorator become
    instances of `Calculator`.
    """

    def __init__(
        self,
        func: types.FunctionType,
        input_types: Dict[str, type],
        output_type: type,
        resource_requirements: Optional[ResourceRequirements] = None,
        inline: bool = True,
    ) -> None:
        if not inspect.isfunction(func):
            raise ValueError("{} is not a function".format(func))

        self._func = func

        self._input_types = input_types
        self._output_type = output_type

        self._inline = inline
        self._resource_requirements = resource_requirements

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

            # Support for list of futures
            if isinstance(argument_map[name], list):
                argument_map[name] = _convert_lists(argument_map[name])

        cast_arguments = self.cast_inputs(argument_map)

        return Future(
            self,
            cast_arguments,
            inline=self._inline,
            resource_requirements=self._resource_requirements,
        )

    def __signature__(self) -> inspect.Signature:
        return inspect.signature(self._func)

    def calculate(self, **kwargs) -> Any:
        output = self.func(**kwargs)

        # Support for lists of futures
        if isinstance(output, list):
            output = _convert_lists(output)

        return output

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


def func(
    func: Callable = None,
    inline: bool = True,
    resource_requirements: Optional[ResourceRequirements] = None,
) -> Union[Callable, Calculator]:
    """
    Sematic Function decorator.
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

        return Calculator(
            func_,
            input_types=input_types,
            output_type=output_type,
            inline=inline,
            resource_requirements=resource_requirements,
        )

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


OutputType = TypeVar("OutputType")


def _make_list(type_: Type[OutputType], list_with_futures: Sequence[Any]) -> OutputType:
    """
    Given a list with futures, returns a future List.
    """
    if not (is_valid_typing_alias(type_) and get_origin_type(type_) is list):
        raise Exception("type_ must be a List type.")

    if not isinstance(list_with_futures, collections.abc.Sequence):
        raise Exception("list_with_futures must be a collections.Sequence.")

    element_type = type_.__args__[0]  # type: ignore

    input_types = {}
    inputs = {}

    for i, item in enumerate(list_with_futures):
        if isinstance(item, Future):
            can_cast, error = can_cast_type(item.calculator.output_type, element_type)
            if not can_cast:
                raise TypeError("Invalid value: {}".format(error))
        else:
            _, error = safe_cast(item, element_type)
            if error is not None:
                raise TypeError("Invalid value: {}".format(error))

        input_types["v{}".format(i)] = element_type
        inputs["v{}".format(i)] = item

    source_code = """
def _make_list({inputs}):
    return [{inputs}]
    """.format(
        inputs=", ".join("v{}".format(i) for i in range(len(list_with_futures)))
    )
    scope: Dict[str, Any] = {"__name__": __name__}
    exec(source_code, scope)
    _make_list = scope["_make_list"]

    return Calculator(
        _make_list, input_types=input_types, output_type=type_, inline=True
    )(**inputs)


def _convert_lists(value_):
    for idx, item in enumerate(value_):
        if isinstance(item, list):
            value_[idx] = _convert_lists(item)

    if any(isinstance(item, Future) for item in value_):
        output_type = None
        for item in value_:
            item_type = (
                item.calculator.output_type if isinstance(item, Future) else type(item)
            )
            if output_type is None:
                output_type = item_type
            elif output_type != item_type:
                output_type = Union[output_type, item_type]

        return _make_list(List[output_type], value_)

    return value_
