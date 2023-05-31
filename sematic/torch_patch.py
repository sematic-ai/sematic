# This code is based on code from:
# https://github.com/pytorch/pytorch/blob/1a6ab8a5dcce45789a6dd61261bc73428439ddb8/torch/__init__.py#L196
# It enables loading of nvidia .so libraries depended on by pytorch when those
# libs are provided via bazel on Linux.
import ctypes
import platform
import os
import sys
import glob

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

def _preload_cuda_deps(lib_folder, lib_name):
    """Preloads cuda deps if they could not be found otherwise."""
    # Should only be called on Linux if default path resolution have failed
    assert platform.system() == 'Linux', 'Should only be called on Linux'
    lib_path = None
    for path in sys.path:
        nvidia_path = os.path.join(path, 'nvidia')
        if not os.path.exists(nvidia_path):
            continue
        candidate_lib_paths = glob.glob(os.path.join(nvidia_path, lib_folder, 'lib', lib_name))
        if candidate_lib_paths and not lib_path:
            lib_path = candidate_lib_paths[0]
        if lib_path:
            break
    if not lib_path:
        raise NotFound(f"{lib_name} not found in the system path {sys.path}")
    ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)

if platform.system() == 'Linux':
    for lib_folder, lib_name in cuda_libs.items():
        try:
            _preload_cuda_deps(lib_folder, lib_name)
        except NotFound:
            pass

