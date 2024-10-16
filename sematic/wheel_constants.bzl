# When updating this, also update versions.py and
# changelog.md.
# This is the version that will be attached to the
# wheel that bazel builds for sematic.
wheel_version_string = "0.40.0"

wheel_author = "Sematic AI, Inc."
wheel_author_email = "support@sematic.dev"
wheel_classifiers = [
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "Programming Language :: Python :: 3 :: Only",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Scientific/Engineering :: Visualization",
    "Typing :: Typed",
]
wheel_description_file = "//:README.rst"
wheel_entry_points = {"console_scripts": ["sematic = sematic.cli.main:cli"]}
wheel_homepage = "https://sematic.dev"
wheel_platform = "any"
wheel_python_requires = ">=3.8,<3.13"
wheel_python_tag = "py3"
wheel_requires = [
    # Specifying this by hand because sematic_py_wheel doesn't know
    # how to fix versions
    "SQLAlchemy>2.0.0",
    "Cython==0.29.33",
]
wheel_deps = [
    "//sematic:client",
    "//sematic:init",
    "//sematic/testing:init",
    "//sematic/cli:main_lib",
    "//sematic/examples/mnist/pytorch:pytorch_lib",
]
