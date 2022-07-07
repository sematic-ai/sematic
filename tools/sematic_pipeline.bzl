load("@rules_python//python:defs.bzl", "py_binary")

load(
    "@io_bazel_rules_docker//lang:image.bzl",
    "app_layer",
)


def sematic_pipeline(name, deps, data = None, base = "@python_39//image", **kwargs):
    """docstring"""
    binary_name = name + ".binary"

    if "main" not in kwargs:
        kwargs["main"] = name + ".py"

    # TODO(mattmoor): Consider using par_binary instead, so that
    # a single target can be used for all three.

    py_binary(
        name = binary_name,
        python_version = "PY3",
        deps = deps,
        data = data,
        #exec_compatible_with = ["@io_bazel_rules_docker//platforms:run_in_container"],
        **kwargs
    )
    # TODO(mattmoor): Consider making the directory into which the app
    # is placed configurable.
    tags = kwargs.get("tags", None)
    for index, dep in enumerate(deps):
        base = app_layer(name = "%s.%d" % (name, index), base = base, dep = dep, tags = tags)
        base = app_layer(name = "%s.%d-symlinks" % (name, index), base = base, dep = dep, binary = binary_name, tags = tags)

    visibility = kwargs.get("visibility", None)
    app_layer(
        name = name,
        base = base,
        entrypoint = ["/usr/bin/python"],
        #env = env,
        binary = binary_name,
        visibility = visibility,
        tags = tags,
        args = kwargs.get("args"),
        data = kwargs.get("data"),
        testonly = kwargs.get("testonly"),
        # The targets of the symlinks in the symlink layers are relative to the
        # workspace directory under the app directory. Thus, create an empty
        # workspace directory to ensure the symlinks are valid. See
        # https://github.com/bazelbuild/rules_docker/issues/161 for details.
        create_empty_workspace_dir = True,
    )