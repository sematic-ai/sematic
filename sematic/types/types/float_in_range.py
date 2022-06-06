# Standard library
import collections
import numbers
import operator
import typing

# Sematic
from sematic.types.generic_type import GenericType
from sematic.types.registry import (
    register_can_cast,
    register_safe_cast,
    register_to_json_encodable_summary,
)
from sematic.types.serialization import value_to_json_encodable
from sematic.types.type import is_type, NotASematicTypeError
from sematic.types.casting import safe_cast


class FloatInRange(float, GenericType):
    _DEFAULT_INCLUSIVE_LOWER = True
    _DEFAULT_INCLUSIVE_UPPER = True

    def __init__(cls, value):
        float.__init__(value)

    @classmethod
    def parametrize(cls, args: typing.Tuple) -> typing.OrderedDict[str, typing.Any]:
        if not isinstance(args, tuple) or len(args) < 2:
            raise ValueError(
                "Not enough arguments to parametrize {}. See https://docs".format(
                    cls.__name__
                )
            )
        if len(args) > 4:
            raise ValueError(
                "Too many arguments to parametrize {}. See https://docs".format(
                    cls.__name__
                )
            )

        lower_bound = args[0]
        upper_bound = args[1]

        if not isinstance(lower_bound, numbers.Real):
            raise ValueError(
                "lower_bound must be a number, got: {}".format(repr(lower_bound))
            )

        if not isinstance(upper_bound, numbers.Real):
            raise ValueError(
                "upper_bound must be a number, got: {}".format(repr(upper_bound))
            )

        lower_bound, upper_bound = float(lower_bound), float(upper_bound)

        if not lower_bound <= upper_bound:
            raise ValueError(
                "lower bound {} should be <= to upper bound {}".format(
                    repr(lower_bound), repr(upper_bound)
                )
            )

        lower_inclusive = args[2] if len(args) >= 3 else cls._DEFAULT_INCLUSIVE_LOWER
        upper_inclusive = args[3] if len(args) >= 4 else cls._DEFAULT_INCLUSIVE_UPPER

        if not isinstance(lower_inclusive, bool):
            raise ValueError(
                "lower_inclusive should be a boolean, got: {}".format(
                    repr(lower_inclusive)
                )
            )

        if not isinstance(upper_inclusive, bool):
            raise ValueError(
                "upper_inclusive should be a boolean, got: {}".format(
                    repr(upper_inclusive)
                )
            )

        parameters = collections.OrderedDict(
            (
                ("lower_bound", lower_bound),
                ("upper_bound", upper_bound),
                ("lower_inclusive", lower_inclusive),
                ("upper_inclusive", upper_inclusive),
            )
        )

        return parameters

    @classmethod
    def lower_bound(cls) -> float:
        return cls.get_parameters()["lower_bound"]

    @classmethod
    def upper_bound(cls) -> float:
        return cls.get_parameters()["upper_bound"]

    @classmethod
    def lower_inclusive(cls) -> bool:
        return cls.get_parameters()["lower_inclusive"]

    @classmethod
    def upper_inclusive(cls) -> bool:
        return cls.get_parameters()["upper_inclusive"]


@register_safe_cast(FloatInRange)
def safe_cast_float_in_rance(
    value: typing.Any, type_: typing.Type[FloatInRange]
) -> typing.Tuple[typing.Optional[typing.Any], typing.Optional[str]]:

    cast_float, error_msg = safe_cast(value, float)
    if error_msg is not None:
        return None, error_msg

    # Getting rid of the typing.Optional constraint
    # garanteed by the check above
    cast_float = typing.cast(float, cast_float)

    (
        lower_bound,
        upper_bound,
        lower_inclusive,
        upper_inclusive,
    ) = type_.get_parameters().values()

    lower_op, upper_op = operator.le, operator.ge
    lower_str, upper_str = "(", ")"

    if lower_inclusive:
        lower_op, lower_str = operator.lt, "["

    if upper_inclusive:
        upper_op, upper_str = operator.gt, "]"

    range_str = "{}{}, {}{}".format(
        lower_str, repr(lower_bound), repr(upper_bound), upper_str
    )

    if lower_op(cast_float, lower_bound) or upper_op(cast_float, upper_bound):
        return None, "{} is not in range {}".format(repr(cast_float), range_str)

    return type_(cast_float), None


@register_can_cast(FloatInRange)
def can_cast_type(
    from_type: typing.Any, to_type: typing.Type[FloatInRange]
) -> typing.Tuple[bool, typing.Optional[str]]:
    if not is_type(from_type):
        raise NotASematicTypeError(from_type)

    if not issubclass(from_type, FloatInRange):
        return False, "{} cannot cast to {}".format(from_type, to_type)

    if from_type.lower_bound() < to_type.lower_bound():
        return (
            False,
            "Incompatible ranges: {}'s lower bound is lower than {}'s".format(
                from_type.__name__, to_type.__name__
            ),
        )

    if (
        from_type.lower_bound() == to_type.lower_bound()
        and to_type.lower_inclusive() is False
        and from_type.lower_inclusive() is True
    ):
        return (
            False,
            (
                "Incompatible ranges:"
                " {} has an exclusive lower bound,"
                " {} has an inclusive lower bound"
            ).format(to_type.__name__, from_type.__name__),
        )

    if from_type.upper_bound() > to_type.upper_bound():
        return (
            False,
            "Incompatible ranges: {}'s upper bound is greater than {}'s".format(
                from_type.__name__, to_type.__name__
            ),
        )

    if (
        from_type.upper_bound() == to_type.upper_bound()
        and to_type.upper_inclusive() is False
        and from_type.upper_inclusive() is True
    ):
        return (
            False,
            (
                "Incompatible ranges:"
                " {} has an exclusive upper bound,"
                " {} has an inclusive upper bound"
            ).format(to_type.__name__, from_type.__name__),
        )

    return True, None


@register_to_json_encodable_summary(FloatInRange)
def _float_in_range_summary(value: float, _) -> float:
    return value_to_json_encodable(value, float)
