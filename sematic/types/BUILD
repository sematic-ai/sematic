sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        ":generic_type",
        ":type",
        "//sematic/types/types:bool",
        "//sematic/types/types:dataclass",
        "//sematic/types/types:enum",
        "//sematic/types/types:float",
        "//sematic/types/types:integer",
        "//sematic/types/types:none",
        "//sematic/types/types:union",
        "//sematic/types/types:list",
        "//sematic/types/types:link",
        "//sematic/types/types:prompt_response",
        "//sematic/types/types:tuple",
        "//sematic/types/types:dict",
        "//sematic/types/types:str",
        "//sematic/types/types:set",
        "//sematic/types/types:datetime",
        "//sematic/types/types:image",
        # Does not actually create a dependency on hugging face
        "//sematic/types/types/huggingface:init",
        # Does not actually create a dependency on torch
        "//sematic/types/types/pytorch:init",
        # Does not actually create a dependency on plotly
        "//sematic/types/types/plotly:init",
        # Does not actually create a dependency on pandas
        "//sematic/types/types/pandas:init",
        # Does not actually create a dependency on matplotlib
        "//sematic/types/types/matplotlib:init",
        # Does not actually create a dependency on snowflake
        "//sematic/types/types/snowflake:init",
        # Does not actually create a dependency on AWS libs
        "//sematic/types/types/aws:init",
    ],
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
    ],
)

sematic_py_lib(
    name = "registry",
    srcs = ["registry.py"],
    deps = [
        ":generic_type",
        ":type",
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
    pip_deps = [
        "cloudpickle",
    ],
    deps = [
        ":generic_type",
        ":registry",
    ],
)
