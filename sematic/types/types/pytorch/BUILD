sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        ":dataloader",
        ":module",
        "//sematic:torch_patch",
    ],
)

sematic_py_lib(
    name = "dataloader",
    srcs = ["dataloader.py"],
    deps = [
        "//sematic/types:registry",
        "//sematic/types:serialization",
        # DO NOT ADD torch HERE
        # This code path is activated in init only if
        # torch is available
    ],
)

sematic_py_lib(
    name = "module",
    srcs = ["module.py"],
    deps = [
        "//sematic/types:registry",
        "//sematic/types:serialization",
        # DO NOT ADD torch HERE
        # This code path is activated in init only if
        # torch is available
    ],
    pip_deps = [
        "cloudpickle",
    ],
)
