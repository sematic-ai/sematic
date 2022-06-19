sematic_py_lib(
    name = "main_lib",
    srcs = ["main.py"],
    deps = [
        ":cli",
        ":start",
        ":stop",
        ":run",
        ":new",
        # Examples
        # These do not add dependencies on 3rd party packages
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
        requirement("click"),
    ]
)

sematic_py_lib(
    name = "start",
    srcs = ["start.py"],
    deps = [
        ":cli",
        ":process_utils",
        "//sematic:config",
        "//sematic/api:server_lib",
        requirement("click"),
    ]
)

sematic_py_lib(
    name = "stop",
    srcs = ["stop.py"],
    deps = [
        ":process_utils",
        ":cli",
        requirement("click"),
    ]
)

sematic_py_lib(
    name = "run",
    srcs = ["run.py"],
    deps = [
        ":cli",
        ":process_utils",
        "//sematic:config",
        requirement("click"),
    ]
)

sematic_py_lib(
    name = "new",
    srcs = ["new.py"],
    deps = [
        ":cli",
        ":examples_utils",
        "//sematic:config",
        requirement("click"),
    ]
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

py_binary(
    name = "main",
    main = "main.py",
    srcs = ["main.py"],
    deps = [
        ":main_lib",
        # This is to make sure we can test via Bazel
        "//sematic/examples/mnist/pytorch:requirements",
        "//sematic/examples/liver_cirrhosis:requirements",
    ]
)