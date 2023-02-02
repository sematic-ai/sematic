# Follow the pattern for extras used by Ray:
# https://github.com/ray-project/ray/blob/efee158cecc49fbec5527e75e17faadba4fac48d/python/ray/serve/__init__.py

try:
    # Sematic
    from sematic.ee.plugins.external_resource.ray.cluster import (  # noqa: F401,E402
        RayCluster,
    )
    from sematic.plugins.abstract_kuberay_wrapper import (  # noqa: F401,E402
        RayClusterConfig,
        RayNodeConfig,
        ScalingGroup,
        SimpleRayCluster,
    )
except ImportError:
    raise ImportError(
        "This import requires Sematic to be installed with `pip install sematic[ray]`"
    )
