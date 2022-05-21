glow_py_lib(
    name = "app",
    srcs = ["app.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("flask"),
        requirement("flask-cors"),
    ]
)

glow_py_lib(
    name = "server_lib",
    srcs = ["server.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//glow/api:app",
        "//glow/api/endpoints:runs",
        "//glow/api/endpoints:artifacts",
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
