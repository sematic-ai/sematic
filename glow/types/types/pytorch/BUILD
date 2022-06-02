glow_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        ":dataloader",
    ]
)

glow_py_lib(
    name = "dataloader",
    srcs = ["dataloader.py"],
    deps = [
        "//glow/types:registry",
        "//glow/types:serialization",
        # DO NOT ADD torch HERE
        # This code path is activated in init only if
        # torch is available
    ]
)