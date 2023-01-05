# Standard Library
from dataclasses import dataclass, field, replace
from typing import Dict, FrozenSet, List, Tuple

# Sematic
from sematic.plugins.abstract_external_resource import (
    AbstractExternalResource,
    ManagedBy,
)
from sematic.resolvers.abstract_resource_manager import AbstractResourceManager


@dataclass(frozen=True)
class _InMemoryResourceRecord:
    """A record of external resources and their associated run(s).

    Attributes
    ----------
    resource:
        The most up-to-date copy of the resource
    run_id_root_id_pairs:
        A FrozenSet where each element is a tuple of (<run id>, <root id>)
    """

    resource: AbstractExternalResource

    # For now, resources can only be used by one run. However, this might
    # be changed at some point, so we want the database to allow for multiple
    # runs per resource. The in-memory representation for the SilentResolver
    # should mirror the database representation in this regard.
    run_id_root_id_pairs: FrozenSet[Tuple[str, str]]


@dataclass
class MemoryResourceManager(AbstractResourceManager):
    resource_id_to_record: Dict[str, _InMemoryResourceRecord] = field(
        default_factory=dict
    )

    def get_resource_for_id(self, resource_id: str) -> AbstractExternalResource:
        return self.resource_id_to_record[resource_id].resource

    def save_resource(self, resource: AbstractExternalResource) -> None:
        if resource.status.managed_by == ManagedBy.SERVER:
            raise ValueError(
                "In-memory resource manager can't manage remotely managed resources"
            )
        if resource.id in self.resource_id_to_record:
            mapping = self.resource_id_to_record[resource.id]
        else:
            mapping = _InMemoryResourceRecord(
                resource=resource, run_id_root_id_pairs=frozenset(())
            )
        self.resource_id_to_record[resource.id] = replace(mapping, resource=resource)

    def link_resource_to_run(self, resource_id: str, run_id: str, root_id: str) -> None:
        mapping = self.resource_id_to_record[resource_id]
        run_id_root_id_pairs = set(mapping.run_id_root_id_pairs)
        new_pair = (run_id, root_id)
        run_id_root_id_pairs.add(new_pair)
        self.resource_id_to_record[resource_id] = replace(
            mapping, run_id_root_id_pairs=frozenset(run_id_root_id_pairs)
        )

    def resources_by_root_id(self, root_id: str) -> List[AbstractExternalResource]:
        resources = []
        for record in self.resource_id_to_record.values():
            for _, associated_root_id in record.run_id_root_id_pairs:
                if associated_root_id == root_id:
                    resources.append(record.resource)
        return resources
