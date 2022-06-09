sematic_py_lib(
    name = "main_lib",
    srcs = ["main.py"],
    deps = [
        ":process_utils",
        "//sematic/api:server_lib",
        "//sematic/db:migrate_lib",
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

py_binary(
    name = "main",
    main = "main.py",
    srcs = ["main.py"],
    deps = [
        ":main_lib",
    ]
)