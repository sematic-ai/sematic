# Standard library
import typing

# Glow
from glow.abstract_future import AbstractFuture, FutureState
from glow.resolver import Resolver


class Future(AbstractFuture):
    """
    Class representing a future.
    """

    def resolve(self, resolver: Resolver, attach: bool = False) -> typing.Any:
        if self.state != FutureState.RESOLVED:
            self.value = resolver.resolve(self)

        if self.state != FutureState.RESOLVED:
            raise RuntimeError("Unresolved Future after resolver call.")

        return self.value

    def set(self, **kwargs):
        mutable_fields = {"name", "inline", "tags"}
        invalid_fields = set(kwargs) - mutable_fields
        if len(invalid_fields) > 0:
            raise ValueError(
                "Cannot mutate thiese fiels on Future: {}".format(invalid_fields)
            )

        for name, value in kwargs.items():
            if name == "tags":
                value = self.tags + value
            setattr(self, name, value)

        return self
