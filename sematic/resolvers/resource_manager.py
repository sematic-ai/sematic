# Standard Library
import abc
from dataclasses import dataclass, field, replace
from typing import Dict, List, Tuple

# Sematic
from sematic.external_resource import ExternalResource


class ResourceManager(abc.ABC):
    """A store for information about external resources and their metadata.

    Abstracts over cloud vs. in-memory implementations. Notably though, this
    abstraction only covers storage and retrieval of resource metadata--it does
    not cover activation/deactivation/state updates of the resources themselves.
    """

    @abc.abstractmethod
    def get_resource_for_id(self, resource_id: str) -> ExternalResource:
        pass

    @abc.abstractmethod
    def save_resource(self, resource: ExternalResource) -> None:
        pass

    @abc.abstractmethod
    def link_resource_to_run(self, resource_id: str, run_id: str, root_id: str) -> None:
        pass

    @abc.abstractmethod
    def resources_by_root_id(self, root_id: str) -> List[ExternalResource]:
        pass


@dataclass(frozen=True)
class _InMemoryResourceRecord:
    """A record of external resources and their associated run(s)

    For now, resources can only be used by one run. However, this might
    be changed at some point, so we want the database to allow for multiple
    runs per resource. The in-memory representation for the SilentResolver
    should mirror the database representation in this regard.

    Attributes
    ----------
    resource:
        The most up-to-date copy of the resource
    run_id_root_id_pairs:
        A tuple where each element is a tuple of (<run id>, <root id>)
    """

    resource: ExternalResource
    run_id_root_id_pairs: Tuple[Tuple[str, str], ...]


@dataclass
class InMemoryResourceManager(ResourceManager):
    resource_id_to_record: Dict[str, _InMemoryResourceRecord] = field(
        default_factory=dict
    )

    def get_resource_for_id(self, resource_id: str) -> ExternalResource:
        return self.resource_id_to_record[resource_id].resource

    def save_resource(self, resource: ExternalResource) -> None:
        if resource.id in self.resource_id_to_record:
            mapping = self.resource_id_to_record[resource.id]
        else:
            mapping = _InMemoryResourceRecord(
                resource=resource, run_id_root_id_pairs=()
            )
        self.resource_id_to_record[resource.id] = replace(mapping, resource=resource)

    def link_resource_to_run(self, resource_id: str, run_id: str, root_id: str) -> None:
        mapping = self.resource_id_to_record[resource_id]
        run_id_root_id_pairs = list(mapping.run_id_root_id_pairs)
        new_pair = (run_id, root_id)
        if new_pair in run_id_root_id_pairs:
            return
        run_id_root_id_pairs.append(new_pair)
        self.resource_id_to_record[resource_id] = replace(
            mapping, run_id_root_id_pairs=tuple(run_id_root_id_pairs)
        )

    def resources_by_root_id(self, root_id: str) -> List[ExternalResource]:
        resources = []
        for record in self.resource_id_to_record.values():
            for _, associated_root_id in record.run_id_root_id_pairs:
                if associated_root_id == root_id:
                    resources.append(record.resource)
        return resources
