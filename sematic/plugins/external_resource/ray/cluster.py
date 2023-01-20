from typing import Optional, Tuple
from dataclasses import dataclass, field, replace
import time
import logging

import kubernetes

from sematic.abstract_plugin import PluginScope
from sematic.scheduling.kubernetes import load_kube_config
from sematic.plugins.abstract_external_resource import AbstractExternalResource, ResourceState, ManagedBy
from sematic.config.settings import get_active_plugins
from sematic.plugins.abstract_kuberay_wrapper import AbstractKuberayWrapper, RayClusterConfig
from sematic.plugins.kuberay_wrapper.standard import StandardKuberayWrapper
from sematic.utils.exceptions import UnsupportedUsageError
from sematic.config.server_settings import ServerSettingsVar, get_server_setting
try:
    import ray
except ImportError as e:
    raise ImportError(
        "RayCluster can only be used in Sematic if your code has a dependency on Ray"
    ) from e


logger = logging.getLogger(__name__)


def _no_default_cluster() -> RayClusterConfig:
    raise ValueError(
        f"RayCluster must be initialized with a {RayClusterConfig.__name__} "
        "for 'cluster'"
    )

@dataclass(frozen=True)
class RayCluster(AbstractExternalResource):

    # Since the parent class has defaults, all params here must technically
    # have defaults. Here we raise an error if no value is provided though.
    cluster: RayClusterConfig = field(default_factory=_no_default_cluster)
    _cluster_url: Optional[str] = None
    
    @classmethod
    def _kuberay_wrapper(cls) -> AbstractKuberayWrapper:
        plugins = get_active_plugins(PluginScope.KUBERAY, default=[StandardKuberayWrapper])
        if len(plugins) == 0:
            raise UnsupportedUsageError(
                f"RayCluster cannot be used unless there is a {AbstractKuberayWrapper.__name__} "
                f"plugin active. Check your settings.yaml file."
            )
        if not issubclass(plugins[0], AbstractKuberayWrapper):
            raise UnsupportedUsageError(
                f"Expected an implementation of '{AbstractKuberayWrapper.__name__}', "
                f"but got: '{plugins[0].__name__}'."
            )
        return plugins[0]
    
    def _do_deactivate(self) -> "RayCluster":
        raise NotImplementedError(
            "Subclasses of ExternalResource should implement ._do_deactivate()"
        )
    
    def _do_ray_init(self) -> "RayCluster":
        if self._cluster_url is not None:
            raise NotImplementedError("TODO")
        else:
            ray.init()
        return self
    
    def __enter__(self: "RayCluster") -> "RayCluster":
        # This is called once activation is DONE. So the cluster should already
        # be around at this point.
        cluster = super().__enter__()
        try:
            cluster = cluster._do_ray_init()
            return cluster
        except Exception:
            self.__exit__()
            raise
    
    def _do_activate(self, is_local: bool) -> "RayCluster":
        if is_local:
            # no activation needs to happen to just
            # use ray.init() locally
            return replace(
                self,
                status=replace(
                    self.status,
                    last_update_epoch_time=int(time.time()),
                    state=ResourceState.ACTIVATING,
                    message="Preparing to use Ray in a local process cluster."
                )
            )
        kuberay_version, error = self._get_kuberay_version()
        if error is not None:
            return replace(
                self,
                status=replace(
                    self.status,
                    last_update_epoch_time=int(time.time()),
                    state=ResourceState.DEACTIVATING,
                    message=error,
                )
            )
        assert kuberay_version is not None
    
    @classmethod
    def _k8s_client(cls) -> kubernetes.client.ApiClient:
        load_kube_config()
        api_client = kubernetes.client.ApiClient()
        return api_client
    
    @classmethod
    def _get_kuberay_version(cls) -> Tuple[Optional[str], Optional[str]]:
        try:
            api_instance = kubernetes.client.AppsV1Api(cls._k8s_client())
            namespace = get_server_setting(ServerSettingsVar.KUBERNETES_NAMESPACE)
            name = cls._kuberay_wrapper().KUBERAY_DEPLOYMENT_NAME
            api_response = api_instance.read_namespaced_deployment(name, namespace)
            if api_response.status.ready_replicas < 1:
                message = (
                    "Kuberay has no ready replicas. Please ask your "
                    "cluster administrator to verify the health of Kuberay, "
                    "and refer to Kuberay docs for troubleshooting: "
                    "https://ray-project.github.io/kuberay/"
                )
                logger.error("Kuberay is not healthy. Status: %s", api_response.status)
                logger.error("Kuberay is not healthy. Message: %s", message)
                return (None, message)
            for container in api_response.spec.template.spec.containers:
                if container.name == cls._kuberay_wrapper().KUBERAY_CONTAINER_NAME:
                    image_tag = container.image.split(":")[-1]
                    return image_tag, None
            return (None, "Kuberay version could not be determined from Kuberay deployment.")
        except Exception as e:
            logger.exception("Error getting Kuberay version: %s", e)
            return None, str(e)
    
    def _do_update(self) -> "RayCluster":
        if self.status.state == ResourceState.ACTIVATING:
            if self.status.managed_by == ManagedBy.RESOLVER:
                return replace(
                    self,
                    status=replace(
                        self.status,
                        last_update_epoch_time=int(time.time()),
                        state=ResourceState.ACTIVE,
                        message="Ready to use Ray in a local process cluster."
                    )
                )
            else:
                raise NotImplementedError("TODO")
