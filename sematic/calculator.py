# Standard Library
import collections
import inspect
import logging
import types
from copy import copy
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

# Sematic
from sematic.abstract_calculator import AbstractCalculator, CalculatorError
from sematic.future import Future
from sematic.resolvers.resource_requirements import ResourceRequirements
from sematic.resolvers.type_utils import make_list_type
from sematic.retry_settings import RetrySettings
from sematic.types.casting import can_cast_type, safe_cast
from sematic.types.registry import validate_type_annotation
from sematic.types.type import is_type


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
        retry_settings: Optional[RetrySettings] = None,
        base_image_tag: Optional[str] = None,
    ) -> None:
        self._validate_func(func)
        self._func = func

        self._input_types = input_types
        self._output_type = output_type

        self._inline = inline
        self._resource_requirements = resource_requirements
        self._retry_settings = retry_settings
        self._base_image_tag = base_image_tag

        self.__doc__ = func.__doc__
        self.__module__ = func.__module__
        self.__name__ = func.__name__
        self._validate()

    def _validate(self):
        for key, annotation in self._input_types.items():
            try:
                validate_type_annotation(annotation)
            except TypeError as e:
                raise TypeError(
                    f"Invalid type annotation for argument '{key}' of {repr(self)}: {e}"
                )
        try:
            validate_type_annotation(self._output_type)
        except TypeError as e:
            raise TypeError(f"Invalid type annotation for output of {repr(self)}: {e}")

    @classmethod
    def _validate_func(cls, func):
        if not inspect.isfunction(func):
            raise TypeError(
                "@sematic.func can only be used with functions. "
                f"But {repr(func)} is a '{type(func).__name__}'."
            )

        if _is_method_like(func):
            raise TypeError(
                "@sematic.func can only be used with functions, not methods. "
                f"But {repr(func)} is a method. Instead, consider defining a "
                "function where the first argument is the object currently being "
                "passed as 'self' or 'cls'. You should also rename that parameter "
                "to something more descriptive"
            )
        if _is_coroutine_like(func):
            raise TypeError(
                "@sematic.func can't be used with async functions, generators, "
                f"or coroutines. But {repr(func)} is one of these."
            )

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

            if isinstance(argument_map[name], tuple):
                argument_map[name] = _convert_tuples(
                    argument_map[name],
                    self._input_types[name],
                )

        cast_arguments = self.cast_inputs(argument_map)

        return Future(
            self,
            cast_arguments,
            inline=self._inline,
            resource_requirements=self._resource_requirements,
            # copying because it will hold state for the particular
            # future (retry_count is mutable and increases with retries)
            retry_settings=copy(self._retry_settings),
            base_image_tag=self._base_image_tag,
        )

    def __signature__(self) -> inspect.Signature:
        return inspect.signature(self._func)

    def calculate(self, **kwargs) -> Any:
        try:
            output = self.func(**kwargs)
        except Exception as e:
            raise CalculatorError(f"Error from running {self.func.__name__}") from e

        # Support for lists of futures
        if isinstance(output, list):
            output = _convert_lists(output)
        if isinstance(output, tuple):
            output = _convert_tuples(output, self.output_type)

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
    func: Optional[Callable] = None,
    inline: bool = True,
    resource_requirements: Optional[ResourceRequirements] = None,
    retry: Optional[RetrySettings] = None,
    base_image_tag: Optional[str] = None,
) -> Union[Callable, Calculator]:
    """
    Sematic Function decorator.
    """
    if inline and resource_requirements is not None:
        raise ValueError(
            "Inline functions cannot have resource requirements "
            "Try using @sematic.func(inline=False, ...)"
        )

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

        if inline and base_image_tag is not None:
            # Not raising an exception because users may be setting `inline` dynamically
            # from CLI args. It would be annoying to have to also change `base_image_tag`
            # dynamically.
            logging.warning(
                "base_image_tag %s for %s will be ignored because inline is True",
                base_image_tag,
                func_.__name__,
            )

        return Calculator(
            func_,
            input_types=input_types,
            output_type=output_type,
            inline=inline,
            resource_requirements=resource_requirements,
            retry_settings=retry,
            base_image_tag=base_image_tag,
        )

    if func is None:
        return _wrapper

    return _wrapper(func)


def _is_method_like(func) -> bool:
    """Return True if and only if 'func' appears to be a method"""
    return (
        inspect.ismethod(func)
        or
        # Why is this second check necessary? Because if somebody uses @func
        # on a method inside the class itself, the method is not yet bound
        # to the class, and inspect's ismethod won't pick it up.
        (
            hasattr(func, "__call__")
            and len(inspect.signature(func).parameters.keys()) >= 1
            and list(inspect.signature(func).parameters.keys())[0] in {"self", "cls"}
        )
    )


def _is_coroutine_like(func) -> bool:
    """Return True if and only if 'func' appears to be async, a coroutine, or similar"""
    return any(
        is_(func)  # type: ignore
        for is_ in (
            inspect.isawaitable,
            inspect.isasyncgenfunction,
            inspect.isasyncgen,
            inspect.iscoroutine,
            inspect.iscoroutinefunction,
            inspect.isgenerator,
            inspect.isgeneratorfunction,
        )
    )


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
                "Variadic arguments are not supported. "
                f"'{func_.__name__}' has variadic argument {repr(arg)}. Please see "
                "https://docs.sematic.dev/diving-deeper/future-algebra#variadic-arguments"
                " for more details."
            )

    return full_arg_spec


OutputType = TypeVar("OutputType")


def _make_list(type_: Type[OutputType], list_with_futures: Sequence[Any]) -> OutputType:
    """
    Given a list with futures, returns a future List.
    """
    if get_origin(type_) is not list:
        raise Exception(
            "type_ must be a List type, and it must be parameterized as List[SomeType]."
        )

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
        return _make_list(make_list_type(value_), value_)

    return value_


TupleOutputType = TypeVar("TupleOutputType")


def _make_tuple(
    type_: Type[TupleOutputType], tuple_with_futures: Sequence[Any]
) -> TupleOutputType:
    """
    Given a tuple with futures, returns a future Tuple.
    """
    if get_origin(type_) is not tuple:
        raise TypeError(
            "type_ must be a Tuple type, and it must be parameterized as "
            f"Tuple[SomeTypeA, SomeTypeB]. Got: {type_}"
        )

    if not isinstance(tuple_with_futures, collections.abc.Sequence):
        raise TypeError("tuple_with_futures must be a collections.Sequence.")

    if len(get_args(type_)) > 1:
        if get_args(type_)[-1] is ...:
            raise TypeError("Sematic does not support Ellipsis in Tuples yet (...)")

    input_types = {}
    inputs = {}

    for i, item in enumerate(tuple_with_futures):
        element_type = get_args(type_)[i]
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
def _make_tuple({inputs}):
    return tuple([{inputs}])
    """.format(
        inputs=", ".join("v{}".format(i) for i in range(len(tuple_with_futures)))
    )
    scope: Dict[str, Any] = {"__name__": __name__}
    exec(source_code, scope)
    _make_tuple = scope["_make_tuple"]

    return Calculator(
        _make_tuple, input_types=input_types, output_type=type_, inline=True
    )(**inputs)


def _convert_tuples(value_, expected_type):
    value_as_list = list(value_)
    for idx, item in enumerate(value_as_list):
        if isinstance(item, tuple):
            value_as_list[idx] = _convert_tuples(item, get_args(expected_type)[idx])
        elif isinstance(item, list):
            value_as_list[idx] = _convert_lists(item)

    if any(isinstance(item, Future) for item in value_as_list):
        return _make_tuple(expected_type, tuple(value_as_list))

    return tuple(value_as_list)
