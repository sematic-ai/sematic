# Standard library
import typing

# Sematic
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.resolvers.local_resolver import LocalResolver
from sematic.resolvers.silent_resolver import SilentResolver
from sematic.resolver import Resolver


class Future(AbstractFuture):
    """
    Class representing a future.

    A future is essentially a tuple of with two elements:

    * The function to execute
    * A set of input arguments, that can be concrete values or futures themselves
    """

    def resolve(
        self, resolver: typing.Optional[Resolver] = None, tracking: bool = True
    ) -> typing.Any:
        """
        Trigger the resolution of the future and all its nested futures.

        Parameters
        ----------
        tracking: bool
            Enable tracking. Defaults to `True`. If `True`, the future's
            execution as well as that of all its nested future will be tracked
            in the database and viewable in the UI. If `False`, no tracking is
            persisted to the DB.
        """
        if self.state != FutureState.RESOLVED:
            default_resolver = LocalResolver if tracking else SilentResolver
            resolver = resolver or default_resolver()

            self.value = resolver.resolve(self)

        return self.value

    def set(self, **kwargs):
        """
        Set future properties: `name`, `tags`.

        Parameters
        ----------
        name: str
            The future's name. This will be used to name the run in the UI.
        tags: list[str]
            A list of strings tags to attach to the resulting run.

        Returns
        -------
        Future
            The current future. This enables chaining.
        """
        mutable_fields = {"name", "inline", "tags", "resource_requirements"}
        invalid_fields = set(kwargs) - mutable_fields
        if len(invalid_fields) > 0:
            raise ValueError("Cannot mutate fields: {}".format(invalid_fields))

        for name, value in kwargs.items():
            if name == "tags":
                if not (
                    isinstance(value, list)
                    and all(isinstance(tag, str) and len(tag) > 0 for tag in value)
                ):
                    raise ValueError(
                        "Invalid tags, must a list of non empty strings: {}".format(
                            repr(value)
                        )
                    )

            if name == "name":
                if not (isinstance(value, str) and len(value) > 0):
                    raise ValueError(
                        "Invalid name, must be a non-empty string: {}".format(
                            repr(value)
                        )
                    )

            # TODO: valdidate inline
            setattr(self._props, name, value)

        return self

    def __getitem__(self, index):
        raise NotImplementedError(
            "Future.__getitem__ is not supported yet. Find a workaround at https://docs.sematic.dev/diving-deeper/future-algebra#attribute-and-item-access"  # noqa: E501
        )

    def __iter__(self):
        raise NotImplementedError(
            "Future.__iter__ is not supported yet. Find a workaround at https://docs.sematic.dev/diving-deeper/future-algebra#unpacking-and-iteration"  # noqa: E501
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
