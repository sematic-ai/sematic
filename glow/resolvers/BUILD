glow_py_lib(
    name = "offline_resolver",
    srcs = ["offline_resolver.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//glow:abstract_future",
        ":state_machine_resolver",
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