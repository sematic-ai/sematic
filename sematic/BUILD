sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        ":calculator",
        ":resolver",
        "//sematic/resolvers:local_resolver",
        "//sematic/types:init",
        "//sematic/types:casting",
    ]
)

sematic_py_lib(
    name = "config",
    srcs = ["config.py"],
    deps = []
)

sematic_py_lib(
    name = "api_client",
    srcs = ["api_client.py"],
    deps = [
        ":config",
        requirement("requests")
    ]
)

sematic_py_lib(
    name = "abstract_calculator",
    srcs = ["abstract_calculator.py"],
    deps = []
)

sematic_py_lib(
    name = "abstract_future",
    srcs = ["abstract_future.py"],
    deps = [
        ":abstract_calculator",
    ]
)

sematic_py_lib(
    name = "calculator",
    srcs = ["calculator.py"],
    deps = [
        ":abstract_calculator",
        ":future",
        "//sematic/types:casting",
        "//sematic/types:registry",
        "//sematic/types:init",
        "//sematic/types:type",
        "//sematic/utils:memoized_property",
    ]
)

sematic_py_lib(
    name = "future",
    srcs = ["future.py"],
    deps = [
        ":abstract_calculator",
        ":abstract_future",
        "//sematic/resolvers:local_resolver",
        "//sematic/resolvers:silent_resolver",
    ]
)

sematic_py_lib(
    name = "resolver",
    srcs = ["resolver.py"],
    deps = [
        ":abstract_future",
    ]
)


sematic_py_wheel(
    name = "wheel",
    visibility = ["//visibility:public"],
    distribution = "sematic",
    python_tag = "py3",
    platform = "any",
    version = "0.2.0",#+{BUILD_TIMESTAMP}",
    python_requires = ">=3.9",
    description_file = "//:README.rst",
    author = "Sematic AI, Inc.",
    license = "MIT",
    author_email = "emmanuel@sematic.ai",
    homepage = "https://github.com/sematic-ai/sematic",
    deps = [
        "//sematic:init",
        "//sematic/cli:main_lib",
    ],
    requires = [
        # Specifying this by hand because sematic_py_wheel doesn't know
        # how to fix versions
        "eventlet==0.30.2",
    ],
    classifiers = [
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Visualization",
        "Typing :: Typed",
    ],
    entry_points={"console_scripts": ["sematic = sematic.cli.main:cli"]},
)
