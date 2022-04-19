# Standard library
import typing

# Glow
from glow.abstract_future import AbstractFuture, FutureState
from glow.resolver import Resolver


class Future(AbstractFuture):
    def resolve(self, resolver: Resolver, attach: bool = False) -> typing.Any:
        if self.state != FutureState.RESOLVED:
            self.value = resolver.resolve(self)

        if self.state != FutureState.RESOLVED:
            raise RuntimeError("Unresolved Future after resolver call.")

        return self.value
