sematic_py_lib(
    name = "snowflake_table",
    srcs = ["snowflake_table.py"],
    data = ["requirements.txt"],
    deps = [
        "//sematic/config:user_settings",
        "//sematic/types:registry",
        "//sematic/types/types:dataclass",
    ]
)

sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        ":snowflake_table",
    ]
)

