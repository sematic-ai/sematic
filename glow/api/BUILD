glow_py_lib(
    name = "app",
    srcs = ["app.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("flask")
    ]
)

glow_py_lib(
    name = "server_lib",
    srcs = ["server.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//glow/api:app",
        "//glow/api/endpoints:runs",
        requirement("flask"),
    ]
)

py_binary(
    name = "server",
    main = "server.py",
    srcs = ["server.py"],
    deps = [
        ":server_lib",
    ]
)
