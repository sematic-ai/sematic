
sematic_py_lib(
    name = "main_lib",
    srcs = ["main.py"],
    deps = [
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
    ]
)

sematic_py_lib(
    name = "cli",
    srcs = ["cli.py"],
    deps = [
        "//sematic:config",
        "//sematic/db:migrate_lib",
    ],
    pip_deps=[
        "click"
    ],
)

sematic_py_lib(
    name = "start",
    srcs = ["start.py"],
    deps = [
        ":cli",
        ":process_utils",
        "//sematic:config",
        "//sematic/api:server_lib",
    ],
    pip_deps=[
        "click"
    ],
)

sematic_py_lib(
    name = "stop",
    srcs = ["stop.py"],
    deps = [
        ":process_utils",
        ":cli",
    ],
    pip_deps=[
        "click"
    ],
)

sematic_py_lib(
    name = "run",
    srcs = ["run.py"],
    deps = [
        ":cli",
        ":process_utils",
        "//sematic:config",
    ],
    pip_deps=[
        "click"
    ],
)

sematic_py_lib(
    name = "new",
    srcs = ["new.py"],
    deps = [
        ":cli",
        ":examples_utils",
        "//sematic:config",
    ],
    pip_deps=[
        "click"
    ],
)

sematic_py_lib(
    name = "process_utils",
    srcs = ["process_utils.py"],
    deps = [
        "//sematic:config",
    ]
)

sematic_py_lib(
    name = "examples_utils",
    srcs = ["examples_utils.py"],
    deps = [
        "//sematic:config",
    ]
)

sematic_py_lib(
    name = "settings",
    srcs = ["settings.py"],
    deps = [
        ":cli",
        "//sematic:user_settings",
    ],
    pip_deps=[
        "click",
        "pyyaml",
    ],
)

sematic_py_binary(
    name = "main",
    main = "main.py",
    srcs = ["main.py"],
    deps = [
        ":main_lib",
        # This is to make sure we can test via Bazel
        "//sematic/examples/mnist/pytorch:requirements",
        "//sematic/examples/liver_cirrhosis:requirements",
    ],
)