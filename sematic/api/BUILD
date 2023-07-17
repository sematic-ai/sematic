sematic_py_lib(
    name = "app",
    srcs = ["app.py"],
    pip_deps = [
        "flask",
        "flask-cors",
    ],
    deps = [],
)

sematic_py_lib(
    name = "server_lib",
    srcs = ["server.py"],
    data = ["//sematic/ui:ui_build"],
    pip_deps = [
        "asgiref",
        "flask",
        "starlette",
        "uvicorn",
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
        "//sematic/api/endpoints:organizations",
        "//sematic/api/endpoints:organizations_users",
        "//sematic/api/endpoints:resolutions",
        "//sematic/api/endpoints:runs",
        "//sematic/api/endpoints:storage",
        "//sematic/api/endpoints:users",
        "//sematic/config:config",
        "//sematic/config:server_settings",
        "//sematic:logs",
        "//sematic/plugins/storage:local_storage",
        "//sematic/plugins:abstract_publisher",
        "//sematic/plugins/publishing:slack",
        "//sematic/utils:daemonize",
    ],
)

py_binary(
    name = "server",
    srcs = ["server.py"],
    data = [],
    main = "server.py",
    deps = [
        ":server_lib",
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
