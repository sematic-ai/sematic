glow_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":generic_type",
        ":type",
        "//glow/types/types:float",
        "//glow/types/types:float_in_range",
        "//glow/types/types:integer",
        "//glow/types/types:list",
        "//glow/types/types:none",
    ]
)

glow_py_lib(
    name = "casting",
    srcs = ["casting.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":registry",
        ":type",
    ],
)

glow_py_lib(
    name = "generic_type",
    srcs = ["generic_type.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":type",
    ]
)

glow_py_lib(
    name = "registry",
    srcs = ["registry.py"],
    visibility = ["//visibility:public"],
    deps = [],
)

glow_py_lib(
    name = "type",
    srcs = ["type.py"],
    visibility = ["//visibility:public"],
    deps = [],
)

glow_py_lib(
    name = "serialization",
    srcs = ["serialization.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":registry",
        requirement("cloudpickle"),
    ],
)
