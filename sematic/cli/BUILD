sematic_py_lib(
    name = "main_lib",
    srcs = ["main.py"],
    # buildifier: leave-alone
    deps = [
        ":cancel",
        ":clean",
        ":cli",
        ":logs",
        ":start",
        ":stop",
        ":run",
        ":migrate",
        ":new",
        ":settings",
        ":version",
        "//sematic/config:config",
        # Examples
        "//sematic/examples/template:template_lib",
        # These do not add dependencies on 3rd party packages
        "//sematic/examples/add:add_lib",
        "//sematic/examples/mnist/pytorch:pytorch_lib",
        "//sematic/examples/liver_cirrhosis:liver_cirrhosis_lib",
    ],
)

sematic_py_lib(
    name = "cli",
    srcs = ["cli.py"],
    pip_deps = [
        "click",
    ],
    deps = [
        "//sematic/db:migrate_lib",
    ],
)

sematic_py_lib(
    name = "cancel",
    srcs = ["cancel.py"],
    pip_deps = [
        "click",
    ],
    deps = [
        ":cli",
        "//sematic:api_client",
    ],
)

sematic_py_lib(
    name = "clean",
    srcs = ["clean.py"],
    pip_deps = [
        "click",
    ],
    deps = [
        ":cli",
        "//sematic:api_client",
        "//sematic:logging",
        "//sematic/api/endpoints:auth",
        "//sematic/config:user_settings",
        "//sematic/config:config",
    ],
)


sematic_py_lib(
    name = "logs",
    srcs = ["logs.py"],
    pip_deps = [
        "click",
    ],
    # buildifier: leave-alone
    deps = [
        ":cli",
        "//sematic:api_client",
        "//sematic:log_reader",
        "//sematic/config:config",
    ],
)

sematic_py_lib(
    name = "start",
    srcs = ["start.py"],
    pip_deps = [
        "click",
    ],
    # buildifier: leave-alone
    deps = [
        ":cli",
        ":process_utils",
        "//sematic/api:server_lib",
        "//sematic/config:config",
    ],
)

sematic_py_lib(
    name = "stop",
    srcs = ["stop.py"],
    pip_deps = [
        "click",
    ],
    deps = [
        ":cli",
        ":process_utils",
    ],
)

sematic_py_lib(
    name = "run",
    srcs = ["run.py"],
    pip_deps = [
        "click",
    ],
    # buildifier: leave-alone
    deps = [
        ":cli",
        ":process_utils",
        "//sematic/config:config",
    ],
)

sematic_py_lib(
    name = "migrate",
    srcs = ["migrate.py"],
    deps = [
        ":cli",
    ],
)

sematic_py_lib(
    name = "new",
    srcs = ["new.py"],
    pip_deps = [
        "click",
    ],
    # buildifier: leave-alone
    deps = [
        ":cli",
        ":examples_utils",
        "//sematic/config:config",
    ],
)

sematic_py_lib(
    name = "process_utils",
    srcs = ["process_utils.py"],
    # buildifier: leave-alone
    deps = [
        "//sematic/config:config",
    ],
)

sematic_py_lib(
    name = "examples_utils",
    srcs = ["examples_utils.py"],
    # buildifier: leave-alone
    deps = [
        "//sematic/config:config",
    ],
)

sematic_py_lib(
    name = "settings",
    srcs = ["settings.py"],
    pip_deps = [
        "click",
        "pyyaml",
    ],
    deps = [
        ":cli",
        "//sematic/config:server_settings",
        "//sematic/config:user_settings",
        "//sematic/plugins/publishing:slack",
    ],
)

sematic_py_lib(
    name = "version",
    srcs = ["version.py"],
    pip_deps = [
        "click",
    ],
    deps = [
        ":cli",
        "//sematic:versions",
    ],
)

sematic_py_binary(
    name = "main",
    srcs = ["main.py"],
    main = "main.py",
    deps = [
        ":main_lib",
        # This is to make sure we can test via Bazel
        "//sematic/examples/mnist/pytorch:requirements",
        "//sematic/examples/liver_cirrhosis:requirements",
    ],
)
