# Standard Library
import abc
import typing

# Sematic
from sematic.abstract_future import AbstractFuture
from sematic.external_resource import ExternalResource


class Resolver(abc.ABC):
    @abc.abstractmethod
    def resolve(self, future: AbstractFuture) -> typing.Any:
        pass

    @abc.abstractclassmethod
    def activate_resource_for_run(
        cls, resource: ExternalResource, run_id: str, root_id: str
    ) -> ExternalResource:
        """Associate the provided resource with the given run and activate it.

        This call will block until the resource is in either the ACTIVE state
        or a terminal state (in the case of failure to activate the resource).
        If the resource can't be activated, will raise ExternalResourceError.

        Parameters
        ----------
        resource:
            The external resource to activate
        run_id:
            The id of the future/run that is using the resource
        root_id:
            The id of the root run for the given run_id

        Returns
        -------
        The active version of the resource

        Raises
        ------
        ExternalResourceError:
            If the external resource could not be activated
        """
        pass

    @abc.abstractclassmethod
    def deactivate_resource(cls, resource_id: str) -> ExternalResource:
        """Deactivate the resource with the given id.

        This call should block until the resource is deactivated or the
        resource has failed to deactivate. If the resource fails to deactivate,
        will raise an ExternalResourceError.

        This may be called even if the resource is already deactivated.

        Parameters
        ----------
        resource_id:
            The id of the resource to deactivate

        Returns
        -------
        The deactivated resource.

        Raises
        ------
        ExternalResourceError:
            If the resource fails to deactivate.
        """
        pass

    def entering_resource_context(cls, resource: ExternalResource):
        """A hook resolvers may use to take action once a resource is activated.

        This will be called after the resource is in the ACTIVE state, but before
        the "with" block for the resource is entered.
        """
        pass

    def exiting_resource_context(cls, resource_id: str):
        """A hook resolvers may use to take action once a resource is no longer used.

        This will be called as the "with" block for the resource is being exited. There
        are no guarantees about the status of the resource in this case.
        """
        pass
