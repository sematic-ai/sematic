sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        ":dataset_reference",
        ":model_reference",
        ":stored_model",
    ],
)

sematic_py_lib(
    name = "dataset_reference",
    srcs = ["dataset_reference.py"],
    deps = [":reference"],
)

sematic_py_lib(
    name = "model_reference",
    srcs = ["model_reference.py"],
    deps = [":reference"],
)

sematic_py_lib(
    name = "stored_model",
    srcs = ["stored_model.py"],
    deps = [
        ":model_reference",
    ],
)

sematic_py_lib(
    name = "reference",
    srcs = ["reference.py"],
    deps = [],
)

# DO NOT ADD torch HERE
# This code path is activated in init only if
# torch is available
