"""
Sematic Public API
"""
import sys

MIN_PYTHON_VERSION = (3, 9, 0)
_CURRENT_PYTHON_VERSION = sys.version_info[0:3]

if _CURRENT_PYTHON_VERSION < MIN_PYTHON_VERSION:
    _min_version_as_str = ".".join(str(i) for i in MIN_PYTHON_VERSION)
    _current_version_as_str = ".".join(str(i) for i in _CURRENT_PYTHON_VERSION)
    raise RuntimeError(
        f"Sematic requires python to be at {_min_version_as_str} or above, "
        f"but you are running {_current_version_as_str}. Please upgrade "
        f"to continue."
    )

from sematic.calculator import func  # noqa: F401,E402
from sematic.resolver import Resolver  # noqa: F401,E402
from sematic.resolvers.local_resolver import LocalResolver  # noqa: F401,E402
from sematic.resolvers.cloud_resolver import CloudResolver  # noqa: F401,E402
from sematic.resolvers.resource_requirements import (  # noqa: F401,E402
    ResourceRequirements,
    KubernetesResourceRequirements,
)
import sematic.types  # noqa: F401,E402
import sematic.future_operators  # noqa: F401,E402
