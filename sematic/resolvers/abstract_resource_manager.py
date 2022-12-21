# Standard Library
import abc
from typing import List

# Sematic
from sematic.external_resource import ExternalResource


class AbstractResourceManager(abc.ABC):
    """A store for information about external resources and their metadata.

    Notably, this abstraction only covers storage and retrieval of resource
    metadata--it does not cover activation/deactivation/state updates of
    the resources themselves.

    Examples of possible implementations would be cloud and in-memory.
    """

    @abc.abstractmethod
    def get_resource_for_id(self, resource_id: str) -> ExternalResource:
        pass

    @abc.abstractmethod
    def save_resource(self, resource: ExternalResource, locally_manage: bool) -> None:
        pass

    @abc.abstractmethod
    def link_resource_to_run(self, resource_id: str, run_id: str, root_id: str) -> None:
        pass

    @abc.abstractmethod
    def resources_by_root_id(self, root_id: str) -> List[ExternalResource]:
        pass
