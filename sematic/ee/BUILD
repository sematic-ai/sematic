load("//sematic:wheel_constants.bzl",
    "wheel_version_string",
    "wheel_author",
    "wheel_author_email",
    "wheel_classifiers",
    "wheel_description_file",
    "wheel_entry_points",
    "wheel_homepage",
    "wheel_platform",
    "wheel_python_requires",
    "wheel_python_tag",
    "wheel_requires",
    "wheel_deps",
)

sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        "//sematic/ee/plugins/external_resource/ray:cluster",
        "//sematic/plugins:abstract_kuberay_wrapper",
    ],
)

sematic_py_wheel(
    name = "wheel",
    author = wheel_author,
    author_email = wheel_author_email,
    classifiers = wheel_classifiers,
    description_file = wheel_description_file,
    distribution = "sematic-ee",
    entry_points = wheel_entry_points,
    homepage = wheel_homepage,
    license = "Proprietary",
    platform = wheel_platform,
    python_requires = wheel_python_requires,
    python_tag = wheel_python_tag,
    requires = wheel_requires + [
        "ray>=2.1.0",
    ],
    version = wheel_version_string,
    visibility = ["//visibility:public"],
    deps = wheel_deps + [
        "//sematic/ee:init",
    ],
)