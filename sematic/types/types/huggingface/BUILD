sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        ":training_arguments"   
    ]
)

sematic_py_lib(
    name = "training_arguments",
    srcs = ["training_arguments.py"],
    deps = [
        "//sematic/types:registry",
        "//sematic/types/types:dataclass",
        # DO NOT ADD transformers here
    ]
)