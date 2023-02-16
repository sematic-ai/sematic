# Standard Library
import logging

logger = logging.getLogger(__name__)

try:
    # Third-party
    import torch  # noqa: F401
except ImportError:
    pass
except Exception as e:
    # Why include errors besides ImportError?
    # Because torch can raise weird things under certain circumstances on
    # import when Cuda is missing:
    #
    # Traceback (most recent call last):
    #     File "site-packages/torch/__init__.py", line 172, in _load_global_deps
    #         ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
    #     File "/lib/python3.9/ctypes/__init__.py", line 374, in __init__
    #         self._handle = _dlopen(self._name, mode)
    # OSError: libcublas.so.11: cannot open shared object file: No such file or directory
    logger.exception("Error importing torch: %s", e)
else:
    # Sematic
    import sematic.types.types.pytorch.dataloader  # noqa: F401
    import sematic.types.types.pytorch.module  # noqa: F401
