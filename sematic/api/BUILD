sematic_py_lib(
    name = "app",
    srcs = ["app.py"],
    pip_deps = [
        "flask",
        "flask-cors",
    ],
    deps = [
        ":wsgi",
    ],
)

sematic_py_lib(
    name = "server_lib",
    srcs = ["server.py"],
    data = ["//sematic/ui:ui_build"],
    pip_deps = [
        "flask",
        "flask-socketio",
        "gevent",
        "gevent-websocket",
    ],
    # buildifier: leave-alone
    deps = [
        ":app",
        "//sematic/api/endpoints:artifacts",
        "//sematic/api/endpoints:auth",
        "//sematic/api/endpoints:edges",
        "//sematic/api/endpoints:events",
        "//sematic/api/endpoints:external_resources",
        "//sematic/api/endpoints:meta",
        "//sematic/api/endpoints:notes",
        "//sematic/api/endpoints:resolutions",
        "//sematic/api/endpoints:runs",
        "//sematic/api/endpoints:storage",
        "//sematic/config:config",
        "//sematic/config:server_settings",
        "//sematic/plugins/storage:local_storage",
        "//sematic/plugins:abstract_publisher",
        "//sematic/plugins/publishing:slack",
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
    pip_deps = [
        "flask",
        "gunicorn",
    ],
    deps = [],
)

# Does not work just yet on M1 mac
# Toolchain resolution issues
#py3_image(
#    name = "server_image",
#    srcs = ["server.py"],
#    deps = [":server_lib"],
#    main = "server.py",
#)
