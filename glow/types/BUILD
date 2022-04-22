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
        "//glow/types/types:null",
    ]
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
    name = "type",
    srcs = ["type.py"],
    visibility = ["//visibility:public"],
    deps = [],
)
