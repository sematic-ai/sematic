load("@//tools:test_rules.bzl", "pytest_test")

pytest_test(
    name = "test_float",
    srcs = ["test_float.py"],
    deps = [
        "//glow/types/types:float",
    ]
)

pytest_test(
    name = "test_float_in_range",
    srcs = ["test_float_in_range.py"],
    deps = [
        "//glow/types:generic_type",
        "//glow/types/types:float",
        "//glow/types/types:float_in_range",
    ]
)

pytest_test(
    name = "test_integer",
    srcs = ["test_integer.py"],
    deps = [
        "//glow/types/types:float",
        "//glow/types/types:integer",
    ]
)

pytest_test(
    name = "test_null",
    srcs = ["test_null.py"],
    deps = [
        "//glow/types/types:null",
    ]
)