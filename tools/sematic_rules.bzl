"""
pytest_test rule
"""

load(
    "@rules_python//python:defs.bzl",
    "py_binary",
    "py_library",
    "py_test",
)

# <add python version>: This will need to be updated when a python version is added
load("@pip_dependencies3_8//:requirements.bzl", requirement3_8 = "requirement")
load("@pip_dependencies3_9//:requirements.bzl", requirement3_9 = "requirement")
load("@pip_dependencies3_10//:requirements.bzl", requirement3_10 = "requirement")
load("@python3_8//:defs.bzl", interpreter3_8 = "interpreter")
load("@python3_9//:defs.bzl", interpreter3_9 = "interpreter")
load("@python3_10//:defs.bzl", interpreter3_10 = "interpreter")

# <add python version>: This section will need to be updated when a python version is added
_PYTHON_VERSION_INFO = dict(
    PY3_8 = struct(
        workspace_name = "python3_8",
        interpreter = interpreter3_8,
        pip_requirement = requirement3_8,
    ),
    PY3_9 = struct(
        workspace_name = "python3_9",
        interpreter = interpreter3_9,
        pip_requirement = requirement3_9,
    ),
    PY3_10 = struct(
        workspace_name = "python3_10",
        interpreter = interpreter3_10,
        pip_requirement = requirement3_10,
    ),
)
PYTHON_VERSION_INFO = struct(**_PYTHON_VERSION_INFO)

# convenience export of a struct containing the version keys
PY3 = struct(**{
    key: key
    for key in _PYTHON_VERSION_INFO.keys()
})

# <default py version change>: This line will need to be updated if we change the default
# python version for sematic.
DEFAULT_PY_VERSION = PY3.PY3_8
requirement = _PYTHON_VERSION_INFO[DEFAULT_PY_VERSION].pip_requirement

ALL_PY3_VERSIONS = sorted([key for key in _PYTHON_VERSION_INFO.keys()], key=lambda k: int(k.replace("PY3_", "")))
PY3_DEFAULT_TEST_VERSIONS = ALL_PY3_VERSIONS

def env_and_runfiles_for_python(version):
    info = _PYTHON_VERSION_INFO[version]
    env = {
        "WHICH_PYTHON": "$(execpath {})".format(info.interpreter),
    }

    runfiles = [
        info.interpreter,
        "@{}//:files".format(info.workspace_name),
    ]

    return (env, runfiles)

def pytest_test(
        name,
        srcs,
        deps = [],
        pip_deps = None,
        args = None,
        data = None,
        env = None,
        py_versions = None,
        **kwargs):
    if pip_deps == None:
        pip_deps = []
    if args == None:
        args = []
    if data == None:
        data = []
    if env == None:
        env = {}
    if py_versions == None:
        py_versions = PY3_DEFAULT_TEST_VERSIONS

    if len(py_versions) < 1:
        fail("There must be at least one python version to test")
    py_versions = sorted(py_versions, key=lambda k: int(k.replace("PY3_", "")))
    for i, py3_version in enumerate(py_versions):
        (pyenv, runfiles) = env_and_runfiles_for_python(py3_version)
        final_deps = full_versioned_deps(
            deps = deps,
            pip_deps = pip_deps + ["pytest", "debugpy"],
            py_version = py3_version,
        )

        # Use the lowest python version provided for the default target,
        # all other python versions should have a suffix like _py3_8
        new_name = name if i == 0 else "{}_{}".format(name, py3_version.lower())
        py_test(
            name = new_name,
            srcs = ["//tools:pytest_runner"] + srcs,
            main = "tools/pytest_runner.py",
            env = dict(env, **pyenv),
            deps = final_deps,
            data = data + runfiles,
            args = args + ["$(location :%s)" % x for x in srcs],
            tags = ["nocov", py3_version.lower()],
            **kwargs
        )

        if i == 0:
            # Only have coverage tests for the lowest version python interpreter
            # These won't get run during a normal bazel test because of our .bazelrc which
            # filters to tests with nocov set. You can execute coverage tests as:
            # bazel coverage //sematic/... --test_output=all --combined_report=lcov --test_tag_filters=cov
            py_test(
                name = "{}_coverage".format(name),
                srcs = ["//tools:pytest_runner"] + srcs,
                main = "tools/pytest_runner.py",
                deps = final_deps + ["//:python_coverage_tools"],
                data = data + runfiles,
                args = args + ["$(location :%s)" % x for x in srcs],
                env = dict(
                    PYTHON_COVERAGE = "$(location //:python_coverage_tools)",
                    **dict(env, **pyenv)
                ),
                tags = ["cov"],
                **kwargs
            )

def sematic_py_lib(name, srcs, deps, pip_deps = None, visibility = None, data = None):
    if pip_deps == None:
        pip_deps = []
    if visibility == None:
        visibility = ["//visibility:public"]
    if data == None:
        data = []

    def create_targets(target_name, pyenv, runfiles, py_version):
        py_library(
            name = target_name,
            srcs = srcs,
            visibility = visibility,
            deps = full_versioned_deps(deps, pip_deps, py_version),
            data = data + runfiles,
        )

        print("{0}_ipython".format(target_name))
        py_binary(
            name = "{0}_ipython".format(target_name),
            main = "//tools/jupyter:ipython.py",
            srcs = ["//tools/jupyter:ipython.py"],
            deps = [
                ":{0}".format(target_name),
            ] + versioned_pip_deps(pip_deps + ["ipython"], py_version),
            env = pyenv,
            tags = ["manual"],
            data = data + runfiles,
        )

    create_multipy_targets(name, create_targets)

def sematic_example(name, requirements = None, data = None, extras = None):
    if data == None:
        data = []
    if extras == None:
        extras = []
    
    sematic_deps = [
        "//sematic:init"
    ] + extras
    sematic_py_lib(
        name = "{}_lib".format(name),
        srcs = native.glob(["*.py", "**/*.py"]),
        data = ["requirements.txt", "README.md", "AUTHORS"] + (data or []),
        deps = sematic_deps,
    )

    sematic_py_lib(
        name = "requirements",
        srcs = ["__main__.py"],
        deps = [],
        pip_deps = [
            req
            for req in (requirements or [])
        ],
    )

    def create_targets(target_name, pyenv, runfiles, py_version):
        py_binary(
            name = target_name,
            main = "__main__.py",
            srcs = ["__main__.py"],
            env = pyenv,
            deps = [
                ":{}_lib_{}".format(name, py_version.lower()),
                ":requirements_{}".format(py_version.lower()),
            ],
            data = data + runfiles,
        )

        py_binary(
            name = "{0}_ipython".format(target_name),
            main = "//tools/jupyter:ipython.py",
            srcs = ["//tools/jupyter:ipython.py"],
            env = pyenv,
            deps = [
                ":{}_lib_{}".format(name, py_version.lower()),
                ":requirements_{}".format(py_version.lower()),
            ] + versioned_pip_deps(
                pip_deps = ["ipython"],
                py_version = py_version,
            ),
            tags = ["manual"],
            data = data + runfiles,
        )

    create_multipy_targets(name, create_targets)

def sematic_py_binary(name, main, srcs, deps, pip_deps = None, data = None, env = None, **kwargs):
    if data == None:
        data = []
    if env == None:
        env = {}
    if pip_deps == None:
        pip_deps = []

    def create_targets(target_name, pyenv, runfiles, py_version):
        full_deps = full_versioned_deps(deps, pip_deps, py_version)

        py_binary(
            name = target_name,
            main = main,
            srcs = srcs,
            deps = full_deps,
            data = data + runfiles,
            env = dict(env, **pyenv),
            **kwargs
        )

    create_multipy_targets(name, create_targets)

def versioned_pip_deps(pip_deps, py_version):
    final_deps = []
    requirement_func = _PYTHON_VERSION_INFO[py_version].pip_requirement
    for pip_dep in pip_deps:
        final_deps.append(requirement_func(pip_dep))
    return final_deps

def versioned_sematic_deps(deps, py_version):
    final_deps = []
    for dep in deps:
        final_deps.append("{}_{}".format(dep, py_version.lower()))
    return final_deps

def full_versioned_deps(deps, pip_deps, py_version):
    return versioned_sematic_deps(deps, py_version) + versioned_pip_deps(pip_deps, py_version)

def create_multipy_targets(base_name, target_creator):
    for i, py_version in enumerate(ALL_PY3_VERSIONS):
        full_name = "{}_{}".format(base_name, py_version.lower())
        (pyenv, runfiles) = env_and_runfiles_for_python(py_version)
        target_creator(full_name, pyenv, runfiles, py_version)
        if i == 0:
            target_creator(base_name, pyenv, runfiles, py_version)
