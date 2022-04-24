# Standard library
import collections
import numbers
import operator
import typing

# Glow
from glow.types.generic_type import GenericType
from glow.types.type import Type, is_type, NotAGlowTypeError
from glow.types.types.float import Float


class FloatInRange(GenericType, Float):
    _DEFAULT_INCLUSIVE_LOWER = True
    _DEFAULT_INCLUSIVE_UPPER = True

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

    @classmethod
    def safe_cast(
        cls, value: typing.Any
    ) -> typing.Tuple[typing.Optional[typing.Any], typing.Optional[str]]:

        cast_float, error_msg = super().safe_cast(value)
        if error_msg is not None:
            return None, error_msg

        # Getting rid of the typing.Optional constraint
        # garanteed by the check above
        cast_float = typing.cast(Float, cast_float)

        (
            lower_bound,
            upper_bound,
            lower_inclusive,
            upper_inclusive,
        ) = cls.get_parameters().values()

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

        return cls(cast_float), None

    @classmethod
    def can_cast_type(
        cls, type_: typing.Type[Type]
    ) -> typing.Tuple[bool, typing.Optional[str]]:
        if not is_type(type_):
            raise NotAGlowTypeError(type_)

        if not issubclass(type_, FloatInRange):
            return False, "{} cannot cast to {}".format(type_, cls)

        if type_.lower_bound() < cls.lower_bound():
            return (
                False,
                "Incompatible ranges: {}'s lower bound is lower than {}'s".format(
                    type_.__name__, cls.__name__
                ),
            )

        if (
            type_.lower_bound() == cls.lower_bound()
            and cls.lower_inclusive() is False
            and type_.lower_inclusive() is True
        ):
            return (
                False,
                (
                    "Incompatible ranges:"
                    " {} has an exclusive lower bound,"
                    " {} has an inclusive lower bound"
                ).format(cls.__name__, type_.__name__),
            )

        if type_.upper_bound() > cls.upper_bound():
            return (
                False,
                "Incompatible ranges: {}'s upper bound is greater than {}'s".format(
                    type_.__name__, cls.__name__
                ),
            )

        if (
            type_.upper_bound() == cls.upper_bound()
            and cls.upper_inclusive() is False
            and type_.upper_inclusive() is True
        ):
            return (
                False,
                (
                    "Incompatible ranges:"
                    " {} has an exclusive upper bound,"
                    " {} has an inclusive upper bound"
                ).format(cls.__name__, type_.__name__),
            )

        return True, None
