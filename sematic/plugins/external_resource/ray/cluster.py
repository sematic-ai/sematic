# Standard Library
import logging
import sys
from dataclasses import dataclass, field, replace
from enum import Enum, unique
from multiprocessing import Process
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


# ray.init should only be called once in any given python
# interpreter. This tracks whether we have done it from the
# current process, to prevent us from doing it multiple times.
_ray_init_called = False

_VALIDATION_INT = 1
_VALIDATION_TIMEOUT_SECONDS = 30.0


@unique
class _ValidationExitCodes(Enum):
    OK = 0
    TIMEOUT = 1
    UNKNOWN_ERROR = 2

    @classmethod
    def message(cls, code: int) -> Optional[str]:
        return {
            _ValidationExitCodes.OK.value: None,
            _ValidationExitCodes.TIMEOUT.value: (
                "Timed out waiting for health validation result."
            ),
            _ValidationExitCodes.UNKNOWN_ERROR.value: (
                "Unknown error when validating cluster health."
            ),
        }[code]


def _no_default_cluster() -> RayClusterConfig:
    raise ValueError(
        f"RayCluster must be initialized with a {RayClusterConfig.__name__} "
        "for 'cluster'"
    )


@dataclass(frozen=True)
class RayCluster(AbstractExternalResource):

    # Since the parent class has defaults, all params here must technically
    # have defaults. Here we raise an error if no value is provided though.
    config: RayClusterConfig = field(default_factory=_no_default_cluster)
    _cluster_name: Optional[str] = None
    _head_uri: Optional[str] = None
    _deleted_cluster: bool = False

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
        global _ray_init_called
        if _ray_init_called:
            return self
        if self._cluster_name is not None:
            logger.info("Connecting to Ray using URI '%s'", self._head_uri)
            ray.init(address=self._head_uri)
        else:
            ray.init()
        _ray_init_called = True
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

    def _request_cluster(
        self, kuberay_version: str, namespace: str, image_uri: Optional[str] = None
    ) -> "RayCluster":
        try:
            run_ids = get_run_ids_for_resource(self.id)

            # should be exactly one run when we activate the cluster
            run = get_run(run_ids[0])
        except Exception as e:
            message = f"Unable to get run when before creating Ray cluster: {e}"
            logger.exception(message)
            return self._with_status(
                ResourceState.DEACTIVATING,
                message,
            )

        try:
            cluster_name = f"ray-{self.id}"
            image_uri = run.container_image_uri if image_uri is None else image_uri
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
            return replace(
                self._with_status(
                    ResourceState.DEACTIVATING,
                    message,
                ),
                _cluster_name=cluster_name,
            )

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
    def _get_kuberay_version(
        cls, namespace: str
    ) -> Tuple[Optional[str], Optional[str]]:
        try:
            api_instance = kubernetes.client.AppsV1Api(cls._k8s_client())
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
            return self._continue_deactivation("Continuing deactivation")

        return self

    def _update_from_activating(self) -> "RayCluster":
        if self.status.managed_by == ManagedBy.RESOLVER:
            return self._with_status(
                ResourceState.ACTIVE, "Ready to use Ray in a local process cluster."
            )
        else:
            is_active, _ = _validate_ray(self)
            if is_active:
                return self._with_status(
                    ResourceState.ACTIVE, "Ready to use remote Ray cluster."
                )
            return self

    def _update_from_active(self) -> "RayCluster":
        is_active, message = _validate_ray(self)
        if is_active:
            return self._with_status(ResourceState.ACTIVE, "Ray cluster is active")
        else:
            return self._continue_deactivation(
                f"Cluster appeared to be unhealthy: {message}."
            )

    def _continue_deactivation(self, reason: str) -> "RayCluster":
        if self.status.managed_by == ManagedBy.RESOLVER or self._deleted_cluster:
            return self._with_status(
                ResourceState.DEACTIVATING, f"Deactivating cluster because: {reason}"
            )

        try:
            namespace = get_server_setting(ServerSettingsVar.KUBERNETES_NAMESPACE)
            self._cluster_api().delete(self._cluster_name, namespace=namespace)
            return self._with_status(
                ResourceState.DEACTIVATING,
                f"Requested deletion of RayCluster with name {self._cluster_name}",
            )
        except ApiException as e:
            if e.status == 404:
                return self._with_status(
                    ResourceState.DEACTIVATED,
                    f"Ray cluster with name '{self._cluster_name}' deleted",
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


@ray.remote
def _validation_task() -> int:
    return _VALIDATION_INT


def _validate_ray_in_subprocess(cluster: RayCluster) -> bool:
    cluster._do_ray_init()
    try:
        result = ray.get(
            [_validation_task.remote()], timeout=_VALIDATION_TIMEOUT_SECONDS
        )[0]
    except GetTimeoutError:
        sys.exit(_ValidationExitCodes.TIMEOUT)
    except Exception:
        logger.exception("Exception during Ray cluster validation")
        sys.exit(_ValidationExitCodes.UNKNOWN_ERROR)
    if result != _VALIDATION_INT:
        sys.exit(_ValidationExitCodes.UNKNOWN_ERROR)
    sys.exit(_ValidationExitCodes.OK)


def _validate_ray(cluster: RayCluster) -> Tuple[bool, Optional[str]]:
    return True, None
    process = Process(target=_validate_ray_in_subprocess, args=(cluster,), daemon=True)
    process.start()

    process.join(1.5 * _VALIDATION_TIMEOUT_SECONDS)
    exit_code = process.exitcode
    if exit_code is None:
        process.kill()
        exit_code = _ValidationExitCodes.TIMEOUT.value
    return (
        exit_code == _ValidationExitCodes.OK,
        _ValidationExitCodes.message(exit_code),
    )
