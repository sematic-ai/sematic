# Standard Library
import abc
import typing

# Sematic
from sematic.abstract_future import AbstractFuture


class Resolver(abc.ABC):
    @abc.abstractmethod
    def resolve(self, future: AbstractFuture) -> typing.Any:
        pass

    @abc.abstractmethod
    def _register_external_resources(self, future: AbstractFuture) -> None:
        """Register any external resources attached to the future.

        For resolvers with remote tracking/execution, this can mean registering
        the resources with the server so the server can start them when needed.

        Parameters
        ----------
        future:
            The future whose external resources should be registered.
        """
        pass
