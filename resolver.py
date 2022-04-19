# Standard library
import abc
import typing

# Glow
from glow.abstract_future import AbstractFuture


class Resolver(abc.ABC):
    @abc.abstractmethod
    def resolve(self, future: AbstractFuture) -> typing.Any:
        pass
