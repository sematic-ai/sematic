# This code is based on code from:
# https://github.com/pytorch/pytorch/blob/1a6ab8a5dcce45789a6dd61261bc73428439ddb8/torch/__init__.py#L196
# It enables loading of nvidia .so libraries depended on by pytorch when those
# libs are provided via bazel on Linux. The pytorch code this is patching is only executed
# on Linux, and is only broken in certain bazel setups.
# Standard Library
import ctypes
import glob
import importlib.util
import logging
import os
import platform
import sys
from itertools import chain


try:
    import bazel_tools  # type: ignore # isort:skip # noqa: F401

    _RUNNING_IN_BAZEL = True
except ImportError:
    _RUNNING_IN_BAZEL = False

# Check whether pytorch is defined; we only want to perform
# the patch if it is. But we don't want to actually
# import it until after the patch.
_torch_spec = importlib.util.find_spec("torch")
_PYTORCH_IS_DEFINED = _torch_spec is not None

logger = logging.getLogger(__name__)


class NotFound(Exception):
    pass


cuda_libs = {
    "cublas": "libcublas.so.*[0-9]",
    "cudnn": "libcudnn.so.*[0-9]",
    "cuda_nvrtc": "libnvrtc.so.*[0-9].*[0-9]",
    "cuda_runtime": "libcudart.so.*[0-9].*[0-9]",
    "cuda_cupti": "libcupti.so.*[0-9].*[0-9]",
    "cufft": "libcufft.so.*[0-9]",
    "curand": "libcurand.so.*[0-9]",
    "cusolver": "libcusolver.so.*[0-9]",
    "cusparse": "libcusparse.so.*[0-9]",
    "nccl": "libnccl.so.*[0-9]",
    "nvtx": "libnvToolsExt.so.*[0-9]",
}


def _preload_cuda_deps(lib_folder, lib_name) -> str:
    """Preloads cuda deps if they could not be found otherwise."""
    # Should only be called on Linux if default path resolution have failed
    assert platform.system() == "Linux", "Should only be called on Linux"
    lib_path = None
    for path in sys.path:
        nvidia_path = os.path.join(path, "nvidia")
        if not os.path.exists(nvidia_path):
            continue
        candidate_lib_paths = glob.glob(
            os.path.join(nvidia_path, lib_folder, "lib", lib_name)
        )
        if candidate_lib_paths and not lib_path:
            lib_path = candidate_lib_paths[0]
        if lib_path:
            break
    if not lib_path:
        raise NotFound(f"{lib_name} not found in the system path {sys.path}")
    ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
    return lib_path


if platform.system() == "Linux" and _RUNNING_IN_BAZEL and _PYTORCH_IS_DEFINED:
    print("Patching torch nvidia loading")
    new_paths = []
    for lib_folder, lib_name in cuda_libs.items():
        try:
            new_paths.append(_preload_cuda_deps(lib_folder, lib_name))
        except NotFound:
            pass
        except Exception as e:
            logger.warning("Error loading %s from %s: %s", lib_name, lib_folder, e)

    # This doesn't fix anything for the current process, but should properly
    # fix things for subprocesses of this process without them needing to
    # re-import this patch file.
    LD_LIBRARY_PATH = os.environ.get("LD_LIBRARY_PATH", "")
    LD_LIBRARY_PATH = ":".join(
        chain([LD_LIBRARY_PATH], [os.path.dirname(p) for p in new_paths])
    )
    os.environ["LD_LIBRARY_PATH"] = LD_LIBRARY_PATH
