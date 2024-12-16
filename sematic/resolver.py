# Standard Library
import abc
import logging
import typing

# Sematic
from sematic.abstract_future import AbstractFuture
from sematic.plugins.abstract_external_resource import AbstractExternalResource


logger = logging.getLogger(__name__)


class Resolver(abc.ABC):
    """
    Abstract base class for all resolvers. Defines the `Resolver` interfaces.
    """

    # TODO: https://github.com/sematic-ai/sematic/issues/975

    def resolve(self, future: AbstractFuture) -> typing.Any:
        """
        Abstract method. Entry-point for the resolution algorithm.

        Parameters
        ----------
        future: AbstractFuture
            Root future of the graph to resolve.

        Returns
        -------
        Any
            output of the pipeline.
        """
        logger.warning(
            "Calling .resolve(...) will soon be deprecated. Please use .run(...) instead."
        )
        return self.run(future)

    @abc.abstractmethod
    def run(self, future: AbstractFuture) -> typing.Any:
        pass

    @classmethod
    def entering_resource_context(cls, resource: AbstractExternalResource):
        """A hook resolvers may use to take action once a resource is activated.

        This will be called after the resource is in the ACTIVE state, but before
        the "with" block for the resource is entered.
        """
        pass

    @classmethod
    def exiting_resource_context(cls, resource_id: str):
        """A hook resolvers may use to take action once a resource is no longer used.

        This will be called as the "with" block for the resource is being exited. There
        are no guarantees about the status of the resource in this case.
        """
        pass
