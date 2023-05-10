sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        ":getitem",
        ":iter",
    ],
)

sematic_py_lib(
    name = "getitem",
    srcs = ["getitem.py"],
    deps = [
        "//sematic:function",
        "//sematic:future",
        "//sematic/types:casting",
    ],
)

sematic_py_lib(
    name = "iter",
    srcs = ["iter.py"],
    deps = [
        "//sematic:future",
        "//sematic/future_operators:getitem",
    ],
)
