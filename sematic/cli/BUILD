sematic_py_lib(
    name = "main_lib",
    srcs = ["main.py"],
    deps = [
        ":cancel",
        ":cli",
        ":start",
        ":stop",
        ":run",
        ":new",
        ":settings",
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
        "//sematic:config",
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
    name = "start",
    srcs = ["start.py"],
    pip_deps = [
        "click",
    ],
    deps = [
        ":cli",
        ":process_utils",
        "//sematic:config",
        "//sematic/api:server_lib",
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
    deps = [
        ":cli",
        ":process_utils",
        "//sematic:config",
    ],
)

sematic_py_lib(
    name = "new",
    srcs = ["new.py"],
    pip_deps = [
        "click",
    ],
    deps = [
        ":cli",
        ":examples_utils",
        "//sematic:config",
    ],
)

sematic_py_lib(
    name = "process_utils",
    srcs = ["process_utils.py"],
    deps = [
        "//sematic:config",
    ],
)

sematic_py_lib(
    name = "examples_utils",
    srcs = ["examples_utils.py"],
    deps = [
        "//sematic:config",
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
        "//sematic:user_settings",
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
