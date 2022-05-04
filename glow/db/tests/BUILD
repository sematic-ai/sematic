glow_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    visibility = ["//visibility:public"],
    data = [
        "//glow/db:schema.sql",
    ],
    deps = [
        "//glow/db:db",
        requirement("pytest"),
    ]
)

pytest_test(
    name = "test_db",
    srcs = ["test_db.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":fixtures",
        "//glow/db:db",
        "//glow/db/models:run",
        "//glow/db:queries",
    ]
)