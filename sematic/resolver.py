# Standard Library
import abc
import typing

# Sematic
from sematic.abstract_future import AbstractFuture


class Resolver(abc.ABC):
    @abc.abstractmethod
    def resolve(self, future: AbstractFuture) -> typing.Any:
        pass
