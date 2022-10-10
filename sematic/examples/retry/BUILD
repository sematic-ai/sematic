load("//bazel:pipeline.bzl", "sematic_pipeline")

sematic_py_lib(
    name = "pipeline",
    srcs = ["pipeline.py"],
    deps = [
        "//sematic:init",
    ],
)

sematic_py_binary(
    name = "__main__",
    srcs = ["__main__.py"],
    main = "__main__.py",
    deps = [
        ":pipeline",
    ],
)
