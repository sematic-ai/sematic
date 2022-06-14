# This should have no external dependencies as it will be
# included in the main sematic wheel
sematic_py_lib(
    name = "main_lib",
    srcs = ["main.py", "pipeline.py"],
    data = ["requirements.txt"],
    deps = [
        "//sematic:init",
    ]
)

sematic_py_lib(
    name = "requirements",
    srcs = ["main.py"],
    deps = [
        requirement("pandas"),
        requirement("statsmodels"),
        requirement("seaborn"),
        requirement("matplotlib"),
    ]
)

# This can contain external dependencies as it will not
# be included in the main wheel.
py_binary(
    name = "main",
    main = "main.py",
    srcs = ["main.py"],
    deps = [
        ":main_lib",
        ":requirements",
    ]
)
