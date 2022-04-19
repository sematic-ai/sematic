load("@//tools:test_rules.bzl", "pytest_test")

pytest_test(
    name = "test_local_resolver",
    srcs = ["test_local_resolver.py"],
    deps = [
        "//glow:calculator",
        "//glow/resolvers:local_resolver",
        "//glow/types/types:float",
    ]
)