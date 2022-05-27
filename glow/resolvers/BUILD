glow_py_lib(
    name = "offline_resolver",
    srcs = ["offline_resolver.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":state_machine_resolver",
        "//glow:abstract_future",
        "//glow/db:queries",
        "//glow/db/models:factories",
        "//glow/db/models:artifact",
        "//glow/db/models:run",
        "//glow/db/models:edge",
    ]
)

glow_py_lib(
    name = "state_machine_resolver",
    srcs = ["state_machine_resolver.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//glow:abstract_future",
        "//glow:resolver",
    ]
)