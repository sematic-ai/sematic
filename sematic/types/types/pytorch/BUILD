sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        ":dataloader",
    ]
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
    ]
)