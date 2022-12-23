# Standard Library
from typing import List

# Sematic
from sematic import api_client
from sematic.external_resource import ExternalResource
from sematic.resolvers.abstract_resource_manager import AbstractResourceManager


class CloudResourceManager(AbstractResourceManager):
    """ResourceManager which uses server APIs to manage external resource metadata"""

    def get_resource_for_id(self, resource_id: str) -> ExternalResource:
        return api_client.get_external_resource(resource_id)

    def save_resource(self, resource: ExternalResource) -> None:
        api_client.save_external_resource(resource)

    def link_resource_to_run(self, resource_id: str, run_id: str, root_id: str) -> None:
        api_client.save_resource_run_link(resource_id, run_id)

    def resources_by_root_id(self, root_id: str) -> List[ExternalResource]:
        ids = api_client.get_resource_ids_by_root_run_id(root_id)
        resources = []
        for resource_id in ids:
            resource = api_client.get_external_resource(resource_id)
            resources.append(resource)
        return resources
