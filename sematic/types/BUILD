sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        ":generic_type",
        ":type",
        "//sematic/types/types:bool",
        "//sematic/types/types:dataclass",
        "//sematic/types/types:float",
        "//sematic/types/types:float_in_range",
        "//sematic/types/types:integer",
        "//sematic/types/types:none",
        "//sematic/types/types:union",
        "//sematic/types/types:list",
        "//sematic/types/types:str",
        # Does not actually create a dependency on torch
        "//sematic/types/types/pytorch:init",
        # Does not actually create a dependency on plotly
        "//sematic/types/types/plotly:init",
        # Does not actually create a dependency on pandas
        "//sematic/types/types/pandas:init",
        # Does not actually create a dependency on matplotlib 
        "//sematic/types/types/matplotlib:init",
        # Does not actually create a dependency on huggingface
        "//sematic/types/types/huggingface:init",
    ]
)

sematic_py_lib(
    name = "casting",
    srcs = ["casting.py"],
    deps = [
        ":registry",
    ],
)

sematic_py_lib(
    name = "generic_type",
    srcs = ["generic_type.py"],
    deps = [
        ":type",
    ]
)

sematic_py_lib(
    name = "registry",
    srcs = ["registry.py"],
    deps = [
        ":generic_type",
    ],
)

sematic_py_lib(
    name = "type",
    srcs = ["type.py"],
    deps = [],
)

sematic_py_lib(
    name = "serialization",
    srcs = ["serialization.py"],
    deps = [
        ":registry",
        ":generic_type",
        requirement("cloudpickle"),
    ],
)
