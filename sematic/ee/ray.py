# Follow the pattern for extras used by Ray:
# https://github.com/ray-project/ray/blob/efee158cecc49fbec5527e75e17faadba4fac48d/python/ray/serve/__init__.py
"""isort:skip_file"""
try:
    # Sematic
    from sematic.ee.plugins.external_resource.ray.cluster import (  # noqa: F401,E402
        RayCluster,
    )
    from sematic.plugins.abstract_kuberay_wrapper import (  # noqa: F401,E402
        AutoscalerConfig,
        RayClusterConfig,
        RayNodeConfig,
        ScalingGroup,
        SimpleRayCluster,
    )
    from sematic.ee.plugins.external_resource.ray import (  # type: ignore  # noqa: F401,E402,E501
        checkpoint,
    )
except ImportError:
    raise ImportError(
        "This import requires Sematic to be installed with `pip install sematic[ray]`"
    )
