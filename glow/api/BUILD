glow_py_lib(
    name = "app",
    srcs = ["app.py"],
    deps = [
        requirement("flask"),
        requirement("flask-cors"),
    ]
)

glow_py_lib(
    name = "server_lib",
    srcs = ["server.py"],
    data = ["//glow/ui:ui_build"],
    deps = [
        "//glow:config",
        "//glow/api:app",
        "//glow/api/endpoints:runs",
        "//glow/api/endpoints:artifacts",
        "//glow/api/endpoints:edges",
        requirement("flask"),
        requirement("flask-socketio"),
        requirement("eventlet")
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
