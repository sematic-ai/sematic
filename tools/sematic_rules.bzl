"""
pytest_test rule
"""

load(
    "@rules_python//python:defs.bzl",
    "py_binary",
    "py_library",
    "py_test",
)
load("@pip_dependencies38//:requirements.bzl", "requirement")
load("@python3_8//:defs.bzl", interpreter38="interpreter")
load("@python3_9//:defs.bzl", interpreter39="interpreter")

def pytest_test(name, srcs, deps = [], args = [], data=None, env=None, **kwargs):
    if data == None:
        data = []
    if env == None:
        env = {}
    py3_version = PY3.PY39
    (pyenv, runfiles) = env_and_runfiles_for_python(py3_version)
    data.extend(runfiles)
    
    py_test(
        name = name,
        srcs = ["//tools:pytest_runner"] + srcs,
        main = "tools/pytest_runner.py",
        env = dict(env, **pyenv),
        deps = deps,
        data = data,
        args = args + ["$(location :%s)" % x for x in srcs],
        tags = ["nocov"],
        **kwargs
    )

    py_test(
        name = "{}_coverage".format(name),
        srcs = ["//tools:pytest_runner"] + srcs,
        main = "tools/pytest_runner.py",
        deps = deps + ["//:python_coverage_tools"],
        args = args + ["$(location :%s)" % x for x in srcs],
        env = dict(
            PYTHON_COVERAGE = "$(location //:python_coverage_tools)",
            **pyenv,
        ),
        tags = ["cov"],
        **kwargs
    )

def sematic_py_lib(name, srcs, deps, visibility = None, data = None):
    if visibility == None:
        visibility = ["//visibility:public"]

    py_library(
        name = name,
        srcs = srcs,
        visibility = visibility,
        deps = deps,
        data = data,
    )

    py_binary(
        name = "{0}_ipython".format(name),
        main = "//tools/jupyter:ipython.py",
        srcs = ["//tools/jupyter:ipython.py"],
        deps = [
            ":{0}".format(name),
            requirement("ipython"),
        ],
        tags = ["manual"],
        data = data,
    )

def sematic_example(name, requirements = None, data = None):
    sematic_py_lib(
        name = "{}_lib".format(name),
        srcs = native.glob(["*.py", "**/*.py"]),
        data = ["requirements.txt", "README", "AUTHORS"] + (data or []),
        deps = [
            "//sematic:init",
        ],
    )

    sematic_py_lib(
        name = "requirements",
        srcs = ["__main__.py"],
        deps = [
            requirement(req)
            for req in (requirements or [])
        ],
    )

    py_binary(
        name = name,
        main = "__main__.py",
        srcs = ["__main__.py"],
        deps = [
            ":{}_lib".format(name),
            ":requirements",
        ],
    )

    py_binary(
        name = "{0}_ipython".format(name),
        main = "//tools/jupyter:ipython.py",
        srcs = ["//tools/jupyter:ipython.py"],
        deps = [
            ":{}_lib".format(name),
            ":requirements",
            requirement("ipython"),
        ],
        tags = ["manual"],
        data = data,
    )

def sematic_py_binary(name, main, srcs, deps, data=None, env=None, **kwargs):
    if data == None:
        data = []
    if env == None:
        env = {}
    py3_version = PY3.PY38
    (pyenv, runfiles) = env_and_runfiles_for_python(py3_version)
    env.update(pyenv)
    data.extend(runfiles)
    py_binary(
        name=name,
        main=main,
        srcs=srcs,
        deps=deps,
        data=data,
        env=dict(env, **pyenv),
        **kwargs,
    )

_PYTHON_VERSION_INFO = dict(
    PY38 = struct(
        workspace_name = "python3_8",
        interpreter = interpreter38,
    ),
    PY39 = struct(
        workspace_name = "python3_9",
        interpreter = interpreter39,
    ),
)
PYTHON_VERSION_INFO = struct(**_PYTHON_VERSION_INFO)

# convenience export of a struct containing the version keys
PY3 = struct(**{
    key: key
    for key in _PYTHON_VERSION_INFO.keys()
})

def env_and_runfiles_for_python(version):
    info = _PYTHON_VERSION_INFO[version]
    env = {
        "WHICH_PYTHON": "$(execpath {})".format(info.interpreter),
        #"PYTHON_VERSION": info.interpreter.version,
    }

    runfiles = [
        info.interpreter,
        "@{}//:files".format(info.workspace_name),
    ]

    return (env, runfiles)