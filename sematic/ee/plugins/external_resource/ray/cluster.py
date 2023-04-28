# Standard Library
import logging
import time
from dataclasses import dataclass, field, replace
from typing import Optional, Tuple, Type

# Third-party
import kubernetes
import ray  # type: ignore
from kubernetes.client.rest import ApiException  # type: ignore
from ray.exceptions import GetTimeoutError  # type: ignore

# Sematic
from sematic.abstract_plugin import PluginScope
from sematic.config.server_settings import ServerSettingsVar, get_server_setting
from sematic.config.settings import get_plugins_with_interface
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
from sematic.utils.retry import retry

logger = logging.getLogger(__name__)


_VALIDATION_INT = 1


def _no_default_cluster() -> RayClusterConfig:
    raise ValueError(
        f"RayCluster must be initialized with a {RayClusterConfig.__name__} "
        f"for 'cluster'"
    )


@dataclass(frozen=True)
class RayCluster(AbstractExternalResource):
    """Represents a distributed Ray cluster.

    For local execution, a local Ray cluster will be used. This class
    is intended to be used via Sematic's "with" api:

    ```python
    @sematic.func(standalone=True)
    def use_ray() -> int:
        with RayCluster(config=CLUSTER_CONFIG):
            return ray.get(some_ray_task.remote())[0]
    ```

    To use it, you must have configured Sematic to use an instance of
    sematic.plugins.abstract_kuberay_wrapper.AbstractKuberayWrapper
    such as sematic.plugins.kuberay_wrapper.standard.StandardKuberayWrapper.

    A Ray cluster will be created before entering the "with" context, and will
    be torn down when that context is exited.

    Attributes
    ----------
    config:
        A configuration for the RayCluster that will be started. If using
        LocalResolver or SilentResolver, this will be ignored and a local
        cluster will be started instead.
    forward_logs:
        Whether or not to have logs from Ray workers returned back to the
        stdout of the Sematic func this resource is used in. Sets
        `log_to_driver` in `ray.init`:
        https://docs.ray.io/en/latest/ray-core/package-ref.html?highlight=init#ray.init
    activation_timeout_seconds:
        The number of seconds the cluster can take to initialize before a timeout error.
    """

    # Since the parent class has defaults, all params here must technically
    # have defaults. Here we raise an error if no value is provided though.
    config: RayClusterConfig = field(default_factory=_no_default_cluster)
    forward_logs: bool = True
    activation_timeout_seconds: float = 15 * 60

    # The name of the remote cluster, if a remote cluster has been requested
    _cluster_name: Optional[str] = None

    # The in-cluster URI of the head node
    _head_uri: Optional[str] = None

    # If the job is remote, this holds the number of pods that are in the "ready"
    # state for the cluster.
    _n_pods: Optional[int] = None

    @classmethod
    def _kuberay_wrapper(cls) -> Type[AbstractKuberayWrapper]:
        plugins = get_plugins_with_interface(
            AbstractKuberayWrapper,
            PluginScope.EXTERNAL_RESOURCE,
            default=[StandardKuberayWrapper],
        )
        if len(plugins) == 0:
            raise UnsupportedUsageError(
                f"RayCluster cannot be used unless there is a "
                f"{AbstractKuberayWrapper.__name__} "
                f"plugin active. Please check your 'settings.yaml' file."
            )
        return plugins[0]

    @retry(exceptions=(ConnectionError,), tries=8, delay=1, backoff=2)
    def _do_ray_init(self) -> "RayCluster":
        """Connect to Ray if not already connected."""
        if ray.is_initialized():
            return self
        try:
            if self._cluster_name is not None:
                logger.info("Connecting to Ray using URI '%s'", self._head_uri)
                ray.init(address=self._head_uri, log_to_driver=self.forward_logs)
            else:
                ray.init(log_to_driver=self.forward_logs)
        except ConnectionError:
            logger.error("Could not connect to Ray...")
            try:
                ray.shutdown()
            except Exception:
                logger.exception(
                    "Error disconnecting from Ray while handling connection error:"
                )
            raise

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
        except Exception:
            logger.exception(
                "While exiting Ray context, could not disconnect from Ray:"
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
                f"creating RayCluster: {e}."
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
        """Request a new cluster from Kuberay."""
        try:
            run_ids = get_run_ids_for_resource(self.id)

            # should be exactly one run when we activate the cluster
            run = get_run(run_ids[0])
        except Exception as e:
            message = f"Unable to get run before creating Ray cluster: {e}."
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
            message = f"Unable to create Kubernetes manifest for RayCluster: {e}."
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
                        f"Cluster not created with expected name '{cluster_name}'.",
                    ),
                    _cluster_name=cluster_name,
                )
        except Exception as e:
            message = f"Unable to request RayCluster with name '{cluster_name}': {e}."
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
    def _k8s_core_client(cls) -> kubernetes.client.CoreV1Api:  # type: ignore
        load_kube_config()
        api_client = kubernetes.client.CoreV1Api()  # type: ignore
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
                logger.error(
                    "Kuberay is not healthy. Status: %s. Message: %s",
                    api_response.status,
                    message,
                )
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
                    "in order to proceed."
                )
                logger.error(message)
                return None, message
            return None, str(e)
        except Exception as e:
            logger.exception("Error getting Kuberay version:")
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
            return self._continue_deactivation(self.status.message)

        return self

    def _update_from_activating(self) -> "RayCluster":
        cluster = self
        if cluster.status.managed_by == ManagedBy.RESOLVER:
            return cluster._with_status(
                ResourceState.ACTIVE, "Ready to use Ray in a local process cluster."
            )
        else:
            cluster = cluster._update_n_pods()
            is_active, _ = cluster._validate_ray()
            if is_active:
                return cluster._with_status(
                    ResourceState.ACTIVE,
                    f"Ready to use remote Ray cluster with name '{self._cluster_name}'.",
                )

            # must be still activating
            return cluster._with_status(
                ResourceState.ACTIVATING,
                (
                    f"Ray cluster has {cluster._n_pods} ready workers "
                    f"(counting the head) out of a minimum of "
                    f"{cluster._min_required_workers()}."
                ),
            )

    def get_activation_timeout_seconds(self) -> float:
        """Get the number of seconds the resource is allowed to take to activate."""
        return self.activation_timeout_seconds

    def _update_n_pods(self) -> "RayCluster":
        if self.status.managed_by == ManagedBy.RESOLVER:
            return self
        api = self._k8s_core_client()
        namespace = get_server_setting(ServerSettingsVar.KUBERNETES_NAMESPACE)
        pods = api.list_namespaced_pod(
            namespace=namespace,
            label_selector=f"ray.io/cluster={self._cluster_name}",
        )

        def pod_is_ready(pod):
            if pod.status.phase != "Running":
                logger.info(
                    "Pod '%s' in cluster '%s' is in phase: %s",
                    pod.metadata.name,
                    self._cluster_name,
                    pod.status.phase,
                )
                return False
            return all(status.ready for status in pod.status.container_statuses)

        if len(pods.items) == 0:
            return replace(self, _n_pods=0)
        pod_count = sum(1 if pod_is_ready(pod) else 0 for pod in pods.items)
        return replace(self, _n_pods=pod_count)

    def _update_from_active(self) -> "RayCluster":
        """Given that this resource is in the ACTIVE state, update the state."""
        cluster = self._update_n_pods()
        is_active, message = cluster._validate_ray()
        if is_active:
            if cluster._n_pods is None:
                return cluster._with_status(
                    ResourceState.ACTIVE, "Ray cluster is active"
                )
            else:
                return cluster._with_status(
                    ResourceState.ACTIVE,
                    f"Ray cluster is active with {cluster._n_pods} "
                    f"ready workers (including the head)",
                )
        else:
            return cluster._continue_deactivation(
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
            return self._with_status(state, f"Deactivating cluster because '{reason}'.")

        try:
            namespace = get_server_setting(ServerSettingsVar.KUBERNETES_NAMESPACE)
            self._cluster_api().delete(self._cluster_name, namespace=namespace)
            return self._with_status(
                ResourceState.DEACTIVATING,
                f"Requested deletion of RayCluster with name '{self._cluster_name}' "
                f"because '{reason}'.",
            )
        except ApiException as e:
            if e.status == 404:
                return self._with_status(
                    ResourceState.DEACTIVATED,
                    f"Ray cluster with name '{self._cluster_name}' "
                    f"deleted because '{reason}'.",
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
                f"had error: {e}."
            )
            logger.exception(message)
            return self._with_status(
                ResourceState.DEACTIVATING,
                message,
            )

    def _do_deactivate(self) -> "RayCluster":
        return self._continue_deactivation(
            "Deactivation requested via the Sematic API."
        )

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

        n_workers = self._n_pods if self._n_pods is not None else 0
        min_workers = self._min_required_workers()
        has_enough_workers = n_workers >= min_workers
        logger.info(f"Ray cluster {self.id} has {n_workers} workers")
        return (
            has_enough_workers,
            None
            if has_enough_workers
            else (
                f"RayCluster has {n_workers} available workers "
                f"(counting the head), but requires at least {min_workers}."
            ),
        )

    def _min_required_workers(self) -> int:
        n_required = 1  # start with 1 for head node
        for group in self.config.scaling_groups:
            n_required += group.min_workers
        return n_required


@ray.remote
def _validation_task() -> int:
    """Simple task just to confirm Ray is usable."""
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
