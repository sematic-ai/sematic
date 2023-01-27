# Standard Library
import logging
import time
from dataclasses import dataclass, field, replace
from typing import Optional, Tuple, Type

# Third-party
import kubernetes
from kubernetes.client.rest import ApiException  # type: ignore

# Sematic
from sematic.abstract_plugin import PluginScope
from sematic.config.server_settings import ServerSettingsVar, get_server_setting
from sematic.config.settings import get_active_plugins
from sematic.db.queries import get_run, get_run_ids_for_resource
from sematic.plugins.abstract_external_resource import (
    AbstractExternalResource,
    ManagedBy,
    ResourceState,
)
from sematic.plugins.abstract_kuberay_wrapper import (
    AbstractKuberayWrapper,
    RayClusterConfig,
)
from sematic.plugins.kuberay_wrapper.standard import StandardKuberayWrapper
from sematic.scheduling.kubernetes import load_kube_config
from sematic.utils.exceptions import UnsupportedUsageError

try:
    # Third-party
    import ray  # type: ignore
    from ray.exceptions import GetTimeoutError  # type: ignore
except ImportError as e:
    raise ImportError(
        "RayCluster can only be used in Sematic if your code has a dependency on Ray"
    ) from e


logger = logging.getLogger(__name__)


_VALIDATION_INT = 1


def _no_default_cluster() -> RayClusterConfig:
    raise ValueError(
        f"RayCluster must be initialized with a {RayClusterConfig.__name__} "
        "for 'cluster'"
    )


@dataclass(frozen=True)
class RayCluster(AbstractExternalResource):
    """Represents an distributed Ray cluster.

    For local execution, a local Ray cluster will be used. This class
    is intended to be used via Sematic's "with" api:

    ```python
    @sematic.func(inline=False)
    def use_ray() -> int:
        with RayCluster(config=CLUSTER_CONFIG):
            return ray.get(some_ray_task.remote())[0]
    ```

    To use it, you must have configured Sematic to use an instance of
    sematic.plugins.abstract_kuberay_wrapper.AbstractKuberayWrapper
    such as sematic.plugins.kuberay_wrapper.standard.StandardKuberayWrapper.

    A cluster will be created before entering the "with" context, and will
    be torn down when that context is exited.

    Attributes
    ----------
    config:
        A configuration for the RayCluster that will be started. If using
        LocalResolver or SilentResolver, this will be ignored and a local
        cluster will be started instead.
    """

    # Since the parent class has defaults, all params here must technically
    # have defaults. Here we raise an error if no value is provided though.
    config: RayClusterConfig = field(default_factory=_no_default_cluster)
    _cluster_name: Optional[str] = None
    _head_uri: Optional[str] = None

    @classmethod
    def _kuberay_wrapper(cls) -> Type[AbstractKuberayWrapper]:
        plugins = get_active_plugins(
            PluginScope.KUBERAY, default=[StandardKuberayWrapper]
        )
        if len(plugins) == 0:
            raise UnsupportedUsageError(
                f"RayCluster cannot be used unless there is a "
                f"{AbstractKuberayWrapper.__name__} "
                f"plugin active. Check your settings.yaml file."
            )
        if not issubclass(plugins[0], AbstractKuberayWrapper):
            raise UnsupportedUsageError(
                f"Expected an implementation of '{AbstractKuberayWrapper.__name__}', "
                f"but got: '{plugins[0].__name__}'."
            )
        return plugins[0]

    def _do_ray_init(self) -> "RayCluster":
        """Connect to Ray if not already connected"""
        if ray.is_initialized():
            return self
        if self._cluster_name is not None:
            logger.info("Connecting to Ray using URI '%s'", self._head_uri)
            ray.init(address=self._head_uri)
        else:
            ray.init()

        logger.info("Initialized connection to Ray for cluster resource %s", self.id)
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

    def __exit__(self, exc_type=None, exc_value=None, exc_traceback=None):
        try:
            # Sleep briefly before shutdown to give
            # workers a little bit of time to forward their final
            # logs to the driver process.
            time.sleep(1)

            # note that this shuts down the cluster for a local cluster,
            # or simply disconnects from it for a remote one.
            ray.shutdown()
        except Exception as e:
            logger.exception(
                "While exiting Ray context, could not disconnect from ray: %s", e
            )
        super().__exit__(exc_type, exc_value, exc_traceback)

    def _do_activate(self, is_local: bool) -> "RayCluster":
        """No-op for local clusters; request a RayCluster from Kuberay for remote."""
        if is_local:
            # no activation needs to happen to just
            # use ray.init() locally
            return self._with_status(
                ResourceState.ACTIVATING,
                "Preparing to use Ray in a local process cluster.",
            )
        try:
            namespace = get_server_setting(ServerSettingsVar.KUBERNETES_NAMESPACE)
        except Exception as e:
            message = (
                f"Namespace for Kubernetes not configured when "
                f"creating RayCluster. {e}"
            )
            logger.exception(message)
            return self._with_status(
                ResourceState.DEACTIVATING,
                message,
            )
        kuberay_version, error = self._get_kuberay_version(namespace)
        if error is not None:
            return self._with_status(
                ResourceState.DEACTIVATING,
                error,
            )
        assert kuberay_version is not None
        return self._request_cluster(kuberay_version, namespace)

    def _request_cluster(self, kuberay_version: str, namespace: str) -> "RayCluster":
        """Request a new cluster from Kuberay"""
        try:
            run_ids = get_run_ids_for_resource(self.id)

            # should be exactly one run when we activate the cluster
            run = get_run(run_ids[0])
        except Exception as e:
            message = f"Unable to get run before creating Ray cluster: {e}"
            logger.exception(message)
            return self._with_status(
                ResourceState.DEACTIVATING,
                message,
            )

        try:
            cluster_name = f"ray-{self.id}"
            image_uri = run.container_image_uri
            assert image_uri is not None  # please mypy
            manifest = self._kuberay_wrapper().create_cluster_manifest(
                image_uri=image_uri,
                cluster_name=cluster_name,
                cluster_config=self.config,
                kuberay_version=kuberay_version,
            )
            head_uri = self._kuberay_wrapper().head_uri(manifest)
        except Exception as e:
            message = f"Unable to create Kubernetes manifest for RayCluster: {e}"
            logger.exception(message)
            return self._with_status(
                ResourceState.DEACTIVATING,
                message,
            )

        try:
            response = self._cluster_api().create(
                manifest,
                namespace=namespace,
            )
            if response.metadata.name != cluster_name:
                return replace(
                    self._with_status(
                        ResourceState.DEACTIVATING,
                        f"Cluster not created with expected name {cluster_name}",
                    ),
                    _cluster_name=cluster_name,
                )
        except Exception as e:
            message = f"Unable to request RayCluster with name {cluster_name}: {e}"
            logger.exception(message)
            return self._continue_deactivation(message)

        return replace(
            self._with_status(
                ResourceState.ACTIVATING,
                f"Requested Ray cluster with name '{cluster_name}'.",
            ),
            _cluster_name=cluster_name,
            _head_uri=head_uri,
        )

    @classmethod
    def _k8s_client(cls) -> kubernetes.client.ApiClient:  # type: ignore
        load_kube_config()
        api_client = kubernetes.client.ApiClient()  # type: ignore
        return api_client

    @classmethod
    def _cluster_api(cls) -> kubernetes.dynamic.DynamicClient:  # type: ignore
        load_kube_config()
        api = kubernetes.dynamic.DynamicClient(  # type: ignore
            cls._k8s_client()
        ).resources.get(api_version="ray.io/v1alpha1", kind="RayCluster")
        return api

    @classmethod
    def _apps_api(cls) -> kubernetes.client.AppsV1Api:  # type: ignore
        return kubernetes.client.AppsV1Api(cls._k8s_client())

    @classmethod
    def _get_kuberay_version(
        cls, namespace: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """Get the version of Kuberay that's currently present on the cluster.

        Parameters
        ----------
        namespace:
            The Kubernetes namespace Kuberay is running in

        Returns
        -------
        A tuple where the two elements will be:
        - the kuberay version as a string, None: if the Kuberay version can be found
        - None, an error message: if the Kuberay version can't be found (ex: Kuberay
        is not installed in the cluster).
        """
        try:
            api_instance = cls._apps_api()
            name = cls._kuberay_wrapper().KUBERAY_DEPLOYMENT_NAME
            api_response = api_instance.read_namespaced_deployment(name, namespace)
            ready: Optional[int] = api_response.status.ready_replicas  # type: ignore

            if ready is None:
                ready = 0

            if ready < 1:
                message = (
                    "Kuberay has no ready replicas. Please ask your "
                    "cluster administrator to verify the health of Kuberay, "
                    "and refer to Kuberay docs for troubleshooting: "
                    "https://ray-project.github.io/kuberay/"
                )
                logger.error("Kuberay is not healthy. Status: %s", api_response.status)
                logger.error("Kuberay is not healthy. Message: %s", message)
                return (None, message)
            for container in api_response.spec.template.spec.containers:  # type: ignore
                if container.name == cls._kuberay_wrapper().KUBERAY_CONTAINER_NAME:
                    image_tag = container.image.split(":")[-1]  # type: ignore
                    return image_tag, None
        except ApiException as e:
            if e.status == 404:
                message = (
                    "Kuberay does not appear to be installed in your Kubernetes "
                    "cluster. Please ask your cluster administrator to install it "
                    "before proceeding."
                )
                logger.error(message)
                return None, message
            return None, str(e)
        except Exception as e:
            logger.exception("Error getting Kuberay version: %s", e)
            return None, str(e)

        return (
            None,
            "Kuberay version could not be determined from Kuberay deployment.",
        )

    def _do_update(self) -> "RayCluster":
        if self.status.state == ResourceState.ACTIVATING:
            return self._update_from_activating()
        elif self.status.state == ResourceState.ACTIVE:
            return self._update_from_active()
        elif self.status.state == ResourceState.DEACTIVATING:
            return self._continue_deactivation("finalizing deactivation")

        return self

    def _update_from_activating(self) -> "RayCluster":
        if self.status.managed_by == ManagedBy.RESOLVER:
            return self._with_status(
                ResourceState.ACTIVE, "Ready to use Ray in a local process cluster."
            )
        else:
            is_active, _ = self._validate_ray()
            if is_active:
                return self._with_status(
                    ResourceState.ACTIVE, "Ready to use remote Ray cluster."
                )

            # must be still activating
            return self

    def _update_from_active(self) -> "RayCluster":
        """Given that this resource is in the ACTIVE state, update the state."""
        is_active, message = self._validate_ray()
        if is_active:
            return self._with_status(ResourceState.ACTIVE, "Ray cluster is active")
        else:
            return self._continue_deactivation(
                f"Cluster appeared to be unhealthy: {message}."
            )

    def _continue_deactivation(self, reason: str) -> "RayCluster":
        """Given that the cluster is in the DEACTIVATING state, update the state.

        If the Kuberay cluster has not been deleted, delete it. If it has been,
        move this object to the DEACTIVATED state.
        """
        if self.status.managed_by == ManagedBy.RESOLVER or self._cluster_name is None:
            state = (
                ResourceState.DEACTIVATED
                if self.status.state == ResourceState.DEACTIVATING
                else ResourceState.DEACTIVATING
            )
            return self._with_status(state, f"Deactivating cluster because: {reason}")

        try:
            namespace = get_server_setting(ServerSettingsVar.KUBERNETES_NAMESPACE)
            self._cluster_api().delete(self._cluster_name, namespace=namespace)
            return self._with_status(
                ResourceState.DEACTIVATING,
                f"Requested deletion of RayCluster with name {self._cluster_name} "
                f"because: {reason}",
            )
        except ApiException as e:
            if e.status == 404:
                return self._with_status(
                    ResourceState.DEACTIVATED,
                    f"Ray cluster with name '{self._cluster_name}' "
                    f"deleted because: {reason}",
                )
            message = (
                f"While attempting to deactivate Ray cluster because '{reason}', "
                f"got {e.status} error from Kubernetes API: '{e.reason}'."
            )
            logger.exception(message)
            return self._with_status(
                ResourceState.DEACTIVATING,
                message,
            )
        except Exception as e:
            message = (
                f"While attempting to deactivate Ray cluster because '{reason}', "
                f"had error: '{e}'."
            )
            logger.exception(message)
            return self._with_status(
                ResourceState.DEACTIVATING,
                message,
            )

    def _do_deactivate(self) -> "RayCluster":
        return self._continue_deactivation("Deactivation requested via Sematic API")

    def _validate_ray(self) -> Tuple[bool, Optional[str]]:
        """Confirm that the Ray cluster is up and appears healthy.

        For local ray, runs a simple task and confirms the expected result
        is obtained. For remote Ray, confirms that the cluster exists and has
        at least 1 available worker (counting the head).

        Returns
        -------
        A tuple where the first element is a boolean indicating whether Ray
        is up and healthy. The second element is None if the cluster is
        healthy, and an error message if not.
        """
        if self.status.managed_by == ManagedBy.RESOLVER:
            return _validate_local_ray(self)

        namespace = get_server_setting(ServerSettingsVar.KUBERNETES_NAMESPACE)

        try:
            cluster_k8s_rep = self._cluster_api().get(
                self._cluster_name, namespace=namespace
            )
        except Exception as e:
            return False, f"Could not get RayCluster: {e}"

        n_workers = cluster_k8s_rep.status.availableWorkerReplicas
        n_workers = n_workers if n_workers is not None else 0
        has_workers = n_workers >= 1
        logger.info(f"Ray cluster {self.id} has {n_workers} workers")
        return (
            has_workers,
            None if has_workers else "RayCluster has no available workers.",
        )


@ray.remote
def _validation_task() -> int:
    """Simple task just to confirm Ray is usable"""
    return _VALIDATION_INT


def _validate_local_ray(cluster: RayCluster) -> Tuple[bool, Optional[str]]:
    try:
        cluster._do_ray_init()
    except Exception as e:
        return False, f"Could not call ray.init(): {e}"
    try:
        result = ray.get([_validation_task.remote()], timeout=30)[0]
    except GetTimeoutError as e:
        message = f"Timeout while executing validation task on Ray cluster: {e}"
        logger.exception(message)
        return False, message
    except Exception as e:
        message = f"Exception during Ray cluster validation: {e}"
        logger.exception(message)
        return False, message
    if result != _VALIDATION_INT:
        message = f"Unexpected result from validation task: '{result}'"
        logger.error(message)
        return False, message
    return True, None
