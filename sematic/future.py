# Standard library
import typing

# Sematic
from sematic.abstract_future import AbstractFuture, FutureState
from sematic.resolvers.local_resolver import LocalResolver
from sematic.resolvers.silent_resolver import SilentResolver


class Future(AbstractFuture):
    """
    Class representing a future.

    A future is essentially a tuple of with two elements:

    * The function to execute
    * A set of input arguments, that can be concrete values or futures themselves
    """

    def resolve(self, tracking: bool = True) -> typing.Any:
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
            resolver = LocalResolver() if tracking else SilentResolver()

            self.value = resolver.resolve(self)

        if self.state != FutureState.RESOLVED:
            raise RuntimeError("Unresolved Future after resolver call.")

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
        mutable_fields = {"name", "inline", "tags"}
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

            setattr(self, name, value)

        return self

    def __getitem__(self, index):
        raise NotImplementedError(
            "Future.__getitem__ is not supported yet. Find a workaround at https://docs.sematic.ai/diving-deeper/future-algebra#attribute-and-item-access"  # noqa: E501
        )
