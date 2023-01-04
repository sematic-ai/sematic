# Standard Library
import logging
import time
from threading import Thread
from typing import List, Set

# Sematic
from sematic import api_client
from sematic.plugins.abstract_external_resource import AbstractExternalResource
from sematic.resolvers.abstract_resource_manager import AbstractResourceManager

logger = logging.getLogger(__name__)


class ServerResourceManager(AbstractResourceManager):
    """ResourceManager which uses server APIs to manage external resource metadata."""

    def __init__(self, update_poll_interval_seconds: int = 600) -> None:
        super().__init__()
        self._update_poll_interval_seconds = update_poll_interval_seconds
        self._resource_ids_updating: Set[str] = set()

    def get_resource_for_id(self, resource_id: str) -> AbstractExternalResource:
        return api_client.get_external_resource(resource_id, refresh_remote=True)

    def save_resource(self, resource: AbstractExternalResource) -> None:
        api_client.save_external_resource(resource)

    def link_resource_to_run(self, resource_id: str, run_id: str, root_id: str) -> None:
        api_client.save_resource_run_links([resource_id], run_id)

    def resources_by_root_id(self, root_id: str) -> List[AbstractExternalResource]:
        return api_client.get_resources_by_root_run_id(root_id)

    def poll_for_updates_by_resource_id(self, resource_id: str):
        """Poll the server for resource state updates on a regular interval.

        Will continue for a given resource until the resource is in a terminal
        state or polling is explicitly stopped.
        """
        start_thread = len(self._resource_ids_updating) == 0
        self._resource_ids_updating.add(resource_id)

        def do_poll():
            while len(self._resource_ids_updating) != 0:
                for id_ in self._resource_ids_updating:
                    logger.info(f"Updating resource state for {id_}")
                    resource = self.get_resource_for_id(id_)
                    if resource.status.state.is_terminal():
                        self.stop_poll_for_updates_by_resource_id(id_)
                time.sleep(self._update_poll_interval_seconds)

        if start_thread:
            thread = Thread(group=None, name="resource-state-updates", target=do_poll)
            thread.setDaemon(True)
            thread.start()

    def stop_poll_for_updates_by_resource_id(self, resource_id: str):
        if resource_id in self._resource_ids_updating:
            self._resource_ids_updating.remove(resource_id)
