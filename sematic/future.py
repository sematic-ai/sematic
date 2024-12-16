# Standard Library
from typing import Any, Optional, Union
from warnings import warn  # noqa: F401

# Sematic
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.resolver import Resolver
from sematic.resolvers.local_resolver import LocalResolver
from sematic.resolvers.resource_requirements import ResourceRequirements
from sematic.resolvers.silent_resolver import SilentResolver


# To avoid creating a dependency of Future on Runner.
# Recall that .resolve will be removed from future, at
# which point there will be no need for such a dependency
# anyway.
# TODO: https://github.com/sematic-ai/sematic/issues/975
Runner = Any


_MUTABLE_FIELDS = {
    "name",
    "standalone",
    "cache",
    "resource_requirements",
    "tags",
    "timeout_mins",
}

INLINE_DEPRECATION_MESSAGE = (
    "The inline argument to the @sematic.func decorator will be deprecated on "
    "June 1st, 2023. Please replace inline=False with standalone=True."
)


class Future(AbstractFuture):
    """
    Class representing a future function execution.

    A future is essentially a tuple of with two elements:

    * The function to execute
    * A set of input arguments, that can be concrete values or futures themselves
    """

    __hash__ = AbstractFuture.__hash__

    def resolve(
        self, resolver: Optional[Union[Resolver, Runner]] = None, tracking: bool = True
    ) -> Any:
        """
        Trigger the resolution of the future and all its nested futures.

        Parameters
        ----------
        resolver: Optional[Resolver]
            The `Resolver` to use to execute this future.
        tracking: bool
            Enable tracking. Defaults to `True`. If `True`, the future's
            execution as well as that of all its nested future will be tracked
            in the database and viewable in the UI. If `False`, no tracking is
            persisted to the DB.
        """
        warn(
            "future.resolve(...) will soon be deprecated. "
            "Please update your code to use runner.run(future) instead.",
            DeprecationWarning,
        )
        if self.state != FutureState.RESOLVED:
            default_resolver = LocalResolver if tracking else SilentResolver
            resolver = resolver or default_resolver()

            self.value = resolver.run(self)

        return self.value

    def set(self, **kwargs):
        """
        Set future properties: `name`, `tags`.

        Parameters
        ----------
        name: str
            The future's name. This will be used to name the run in the UI.
        standalone: bool
            When using the `CloudRunner`, whether the instrumented function
            should be executed in a standalone container or inside the same
            process and worker that is executing the `Runner` itself.

            Defaults to `False`, as most pipeline functions are expected to be
            lightweight. Set to `True` in order to distribute
            its execution to a worker and parallelize its execution.
        cache: bool
            Whether to cache the function's output value under the
            `cache_namespace` configured in the `Runner`. Defaults to `False`.

            Do not activate this on a non-deterministic function!
        resource_requirements: ResourceRequirements
            When using the `CloudRunner`, specifies what special execution
            resources the function requires. Defaults to `None`.
        tags: List[str]
            A list of strings tags to attach to the resulting run.

        Returns
        -------
        Future
            The current `Future` object. This enables chaining.
        """
        invalid_fields = set(kwargs) - _MUTABLE_FIELDS
        if len(invalid_fields) > 0:
            raise ValueError(f"Cannot mutate fields: {invalid_fields}")

        if "name" in kwargs:
            value = kwargs["name"]
            if not (isinstance(value, str) and len(value) > 0):
                raise ValueError(
                    f"Invalid `name`, must be a non-empty string: {repr(value)}"
                )

        if "inline" in kwargs:
            warn(INLINE_DEPRECATION_MESSAGE, DeprecationWarning)
            value = kwargs["inline"]
            del kwargs["inline"]
            kwargs["standalone"] = value

        if "standalone" in kwargs:
            value = kwargs["standalone"]
            if not (isinstance(value, bool)):
                raise ValueError(f"Invalid `standalone`, must be a bool: {repr(value)}")

        if "cache" in kwargs:
            value = kwargs["cache"]
            if not (isinstance(value, bool)):
                raise ValueError(f"Invalid `cache`, must be a bool: {repr(value)}")

        if "resource_requirements" in kwargs:
            value = kwargs["resource_requirements"]
            if not (isinstance(value, ResourceRequirements)):
                raise ValueError(
                    f"Invalid `resource_requirements`, must be a ResourceRequirements: "
                    f"{repr(value)}"
                )

        if "tags" in kwargs:
            value = kwargs["tags"]
            if not (
                isinstance(value, list)
                and all(isinstance(tag, str) and len(tag) > 0 for tag in value)
            ):
                raise ValueError(
                    f"Invalid `tags`, must be a list of non empty strings: {repr(value)}"
                )

        # at this point, kwargs contains only mutable properties,
        # and they have all been checked
        for name, value in kwargs.items():
            setattr(self._props, name, value)

        return self

    def __getitem__(self, index):
        raise NotImplementedError(
            "Future.__getitem__ is not supported yet. Find a workaround at https://docs.sematic.dev/diving-deeper/future-algebra#attribute-access"  # noqa: E501
        )

    def __iter__(self):
        raise NotImplementedError(
            "Future.__iter__ is not supported yet. Find a workaround at https://docs.sematic.dev/diving-deeper/future-algebra#unpacking-and-iteration-on-lists"  # noqa: E501
        )

    def __bool__(self):
        raise NotImplementedError(
            "Future.__bool__ is not supported yet. Find a workaround at https://docs.sematic.dev/diving-deeper/future-algebra#arithmetic-operations"  # noqa: E501
        )

    def __not__(self):
        raise NotImplementedError(
            "Future.__not__ is not supported yet. Find a workaround at https://docs.sematic.dev/diving-deeper/future-algebra#arithmetic-operations"  # noqa: E501
        )

    def __add__(self, _):
        raise NotImplementedError(
            "Future.__add__ is not supported yet. Find a workaround at https://docs.sematic.dev/diving-deeper/future-algebra#arithmetic-operations"  # noqa: E501
        )

    def __iadd__(self, _):
        raise NotImplementedError(
            "Future.__iadd__ is not supported yet. Find a workaround at https://docs.sematic.dev/diving-deeper/future-algebra#arithmetic-operations"  # noqa: E501
        )

    def __mul__(self, _):
        raise NotImplementedError(
            "Future.__mul__ is not supported yet. Find a workaround at https://docs.sematic.dev/diving-deeper/future-algebra#arithmetic-operations"  # noqa: E501
        )

    def __imul__(self, _):
        raise NotImplementedError(
            "Future.__imul__ is not supported yet. Find a workaround at https://docs.sematic.dev/diving-deeper/future-algebra#arithmetic-operations"  # noqa: E501
        )

    def __truediv__(self, _):
        raise NotImplementedError(
            "Future.__truediv__ is not supported yet. Find a workaround at https://docs.sematic.dev/diving-deeper/future-algebra#arithmetic-operations"  # noqa: E501
        )

    def __itruediv__(self, _):
        raise NotImplementedError(
            "Future.__itruediv__ is not supported yet. Find a workaround at https://docs.sematic.dev/diving-deeper/future-algebra#arithmetic-operations"  # noqa: E501
        )

    def __eq__(self, _value: Any):
        if isinstance(_value, AbstractFuture):
            return super(Future, self).__eq__(_value)
        raise NotImplementedError(
            "Future.__eq__ is not supported yet. Find a workaround at https://docs.sematic.dev/diving-deeper/future-algebra#arithmetic-operations"  # noqa: E501
        )

    def __gt__(self, _):
        raise NotImplementedError(
            "Future.__gt__ is not supported yet. Find a workaround at https://docs.sematic.dev/diving-deeper/future-algebra#arithmetic-operations"  # noqa: E501
        )

    def __ge__(self, _):
        raise NotImplementedError(
            "Future.__ge__ is not supported yet. Find a workaround at https://docs.sematic.dev/diving-deeper/future-algebra#arithmetic-operations"  # noqa: E501
        )

    def __lt__(self, _):
        raise NotImplementedError(
            "Future.__lt__ is not supported yet. Find a workaround at https://docs.sematic.dev/diving-deeper/future-algebra#arithmetic-operations"  # noqa: E501
        )

    def __le__(self, _):
        raise NotImplementedError(
            "Future.__le__ is not supported yet. Find a workaround at https://docs.sematic.dev/diving-deeper/future-algebra#arithmetic-operations"  # noqa: E501
        )
