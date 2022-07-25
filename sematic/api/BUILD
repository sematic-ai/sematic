sematic_py_lib(
    name = "app",
    srcs = ["app.py"],
    deps = [
        ":wsgi",
        requirement("flask"),
        requirement("flask-cors"),
    ],
)

sematic_py_lib(
    name = "server_lib",
    srcs = ["server.py"],
    data = ["//sematic/ui:ui_build"],
    deps = [
        "//sematic:config",
        "//sematic/api:app",
        "//sematic/api/endpoints:artifacts",
        "//sematic/api/endpoints:auth",
        "//sematic/api/endpoints:edges",
        "//sematic/api/endpoints:notes",
        "//sematic/api/endpoints:runs",
        requirement("flask"),
        requirement("flask-socketio"),
        requirement("eventlet"),
    ],
)

py_binary(
    name = "server",
    srcs = ["server.py"],
    main = "server.py",
    deps = [
        ":server_lib",
    ],
)

sematic_py_lib(
    name = "wsgi",
    srcs = ["wsgi.py"],
    deps = [
        requirement("flask"),
        requirement("gunicorn"),
    ],
)

# Does not work just yet on M1 mac
# Toolchain resolution issues
#py3_image(
#    name = "server_image",
#    srcs = ["server.py"],
#    deps = [":server_lib"],
#    main = "server.py",
#)
