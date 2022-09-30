load("//sematic:wheel_version.bzl", "wheel_version_string")

sematic_py_lib(
    name="init",
    srcs=["__init__.py"],
    deps=[
        ":calculator",
        ":container_images",
        ":resolver",
        ":retry_settings",
        "//sematic/future_operators:init",
        "//sematic/resolvers:cloud_resolver",
        "//sematic/resolvers:local_resolver",
        "//sematic/resolvers:resource_requirements",
        "//sematic/resolvers:worker",
        "//sematic/types:casting",
        "//sematic/types:init",
    ],
)

sematic_py_lib(
    name="config",
    srcs=["config.py"],
    deps=[
        ":config_dir",
        ":user_settings",
    ],
)

sematic_py_lib(
    name="config_dir",
    srcs=["config_dir.py"],
    deps=[],
)

sematic_py_lib(
    name="container_images",
    srcs=["container_images.py"],
    deps=[],
)

sematic_py_lib(
    name="user_settings",
    srcs=["user_settings.py"],
    pip_deps=[
        "pyyaml",
    ],
    deps=[
        ":config_dir",
    ],
)

sematic_py_lib(
    name="api_client",
    srcs=["api_client.py"],
    pip_deps=[
        "requests",
    ],
    deps=[
        ":config",
        "//sematic:versions",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:factories",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic/utils:retry",
    ],
)

sematic_py_lib(
    name="log_reader",
    srcs=["log_reader.py"],
    deps=[
        "//sematic:storage",
        "//sematic:abstract_future",
        "//sematic/db:queries",
        "//sematic/resolvers:cloud_resolver",
        "//sematic/scheduling:external_job",
    ],
    pip_deps=[
        "requests",
    ],
)


sematic_py_lib(
    name="client",
    srcs=["client.py"],
    deps=[
        ":api_client",
    ],
)

sematic_py_lib(
    name="abstract_calculator",
    srcs=["abstract_calculator.py"],
    deps=[],
)

sematic_py_lib(
    name="abstract_future",
    srcs=["abstract_future.py"],
    deps=[
        ":abstract_calculator",
        ":retry_settings",
        "//sematic/resolvers:resource_requirements",
    ],
)

sematic_py_lib(
    name="calculator",
    srcs=["calculator.py"],
    deps=[
        ":abstract_calculator",
        ":future",
        ":retry_settings",
        "//sematic/resolvers:resource_requirements",
        "//sematic/types:casting",
        "//sematic/types:init",
        "//sematic/types:registry",
        "//sematic/types:type",
        "//sematic/utils:memoized_property",
    ],
)

sematic_py_lib(
    name="future",
    srcs=["future.py"],
    deps=[
        ":abstract_calculator",
        ":abstract_future",
        "//sematic:resolver",
        "//sematic/resolvers:local_resolver",
        "//sematic/resolvers:silent_resolver",
    ],
)

sematic_py_lib(
    name="resolver",
    srcs=["resolver.py"],
    deps=[
        ":abstract_future",
    ],
)

sematic_py_lib(
    name="retry_settings",
    srcs=["retry_settings.py"],
    deps=[
        "//sematic/utils:exceptions",
    ],
)

sematic_py_lib(
    name="storage",
    srcs=["storage.py"],
    deps=[
        ":user_settings",
        "//sematic/utils:retry",
    ],
    pip_deps=[
        "boto3",
    ],
)

sematic_py_lib(
    name="versions",
    srcs=["versions.py"],
    deps=[],
)

sematic_py_wheel(
    name="wheel",
    author="Sematic AI, Inc.",
    author_email="emmanuel@sematic.ai",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Visualization",
        "Typing :: Typed",
    ],
    description_file="//:README.rst",
    distribution="sematic",
    entry_points={"console_scripts": ["sematic = sematic.cli.main:cli"]},
    homepage="https://sematic.dev",
    license="Apache License 2.0",
    platform="any",
    python_requires=">=3.8,<3.10",
    python_tag="py3",
    requires=[
        # Specifying this by hand because sematic_py_wheel doesn't know
        # how to fix versions
        "eventlet==0.30.2",
    ],
    version=wheel_version_string,
    visibility=["//visibility:public"],
    deps=[
        "//sematic:client",
        "//sematic:init",
        "//sematic/cli:main_lib",
    ],
)
