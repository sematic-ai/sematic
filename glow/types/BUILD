glow_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        ":generic_type",
        ":type",
        "//glow/types/types:dataclass",
        "//glow/types/types:float",
        "//glow/types/types:float_in_range",
        "//glow/types/types:integer",
        "//glow/types/types:list",
        "//glow/types/types:str",
    ]
)

glow_py_lib(
    name = "casting",
    srcs = ["casting.py"],
    deps = [
        ":registry",
    ],
)

glow_py_lib(
    name = "generic_type",
    srcs = ["generic_type.py"],
    deps = [
        ":type",
    ]
)

glow_py_lib(
    name = "registry",
    srcs = ["registry.py"],
    deps = [
        ":generic_type",
    ],
)

glow_py_lib(
    name = "type",
    srcs = ["type.py"],
    deps = [],
)

glow_py_lib(
    name = "serialization",
    srcs = ["serialization.py"],
    deps = [
        ":registry",
        ":generic_type",
        requirement("cloudpickle"),
    ],
)
