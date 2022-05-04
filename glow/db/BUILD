glow_py_lib(
    name = "db",
    srcs = ["db.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("sqlalchemy"),
        "//glow/utils:config_dir",
    ]
)

glow_py_lib(
    name = "queries",
    srcs = ["queries.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":db",
        "//glow/db/models:run",
    ]
)

exports_files(["schema.sql"])
