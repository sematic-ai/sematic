load("@rules_python//python:packaging.bzl", "py_wheel", "py_package")

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

py_package(
    name = "server_package",
    deps = [
        ":server_lib",
    ]
)

py_wheel(
    name = "sematic_server",
    distribution = "sematic-server",
    version = "0.0.1",
    deps = [
        ":server_package",
    ]
)

# Does not work just yet on M1 mac
# Toolchain resolution issues
#py3_image(
#    name = "server_image",
#    srcs = ["server.py"],
#    deps = [":server_lib"],
#    main = "server.py",
#)
