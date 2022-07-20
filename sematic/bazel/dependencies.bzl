load("@python3_9//:defs.bzl", "interpreter")
load("@rules_python//python:pip.bzl", "pip_parse")
load(
    "@io_bazel_rules_docker//python3:image.bzl",
    py_image_repos = "repositories",
)

def sematic_pip_parse():
    pip_parse(
        name = "pip_dependencies",
        python_interpreter_target = interpreter,
        requirements_lock = "@sematic//requirements:requirements.txt",
    )
    py_image_repos()
