glow_py_lib(
    name = "db",
    srcs = ["db.py"],
    deps = [
        requirement("sqlalchemy"),
        "//glow/utils:config_dir",
    ]
)

glow_py_lib(
    name = "queries",
    srcs = ["queries.py"],
    deps = [
        ":db",
        "//glow/db/models:artifact",
        "//glow/db/models:edge",
        "//glow/db/models:run",
        requirement("sqlalchemy"),

    ]
)

exports_files(["schema.sql"])
