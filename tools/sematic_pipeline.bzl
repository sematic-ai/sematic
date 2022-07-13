load(
    "@io_bazel_rules_docker//python3:image.bzl",
    "py3_image",
)
load("@io_bazel_rules_docker//container:push.bzl", "container_push")
load("@rules_python//python:defs.bzl", "py_binary")
load("@io_bazel_rules_docker//container:providers.bzl", "PushInfo")

def sematic_pipeline(
        name,
        deps,
        registry,
        repository = None,
        data = None,
        base = "@sematic-worker-base//image",
        srcs = None):
    """docstring"""
    py3_image(
        name = "{}_image".format(name),
        main = "//sematic/resolvers:worker.py",
        srcs = ["//sematic/resolvers:worker.py"],
        data = data,
        deps = deps + ["//sematic/resolvers:worker"],
        visibility = ["//visibility:public"],
        base = base,
        # TODO: parametrize instead of hard-code prefix
        env = {
            "PYTHONHOME": "/app/sematic/examples/bazel/{}_image.binary.runfiles/python_interpreter/bazel_install".format(name),
        },
        tags = ["manual"],
    )

    container_push(
        name = "{}_push".format(name),
        image = "{}_image".format(name),
        registry = registry,
        repository = repository or "sematic",
        tag = name,
        format = "Docker",
        tags = ["manual"],
    )

    container_push_at_build(
        name = "{}_push_at_build".format(name),
        container_push = ":{}_push".format(name),
        tags = ["manual"],
    )

    py_binary(
        name = name,
        srcs = srcs or ["{}.py".format(name)],
        deps = deps,
        data = [":{}_push_at_build".format(name)],
        tags = ["manual"],
    )

    py_binary(
        name = "{}_local".format(name),
        main = "{}.py".format(name),
        srcs = ["{}.py".format(name)],
        deps = deps,
    )

def _container_push_at_build(ctx):
    marker = ctx.actions.declare_file("{0}.marker".format(ctx.label.name))
    ctx.actions.run_shell(
        command = "{} && touch {}".format(ctx.executable.container_push.path, marker.path),
        tools = [ctx.executable.container_push],
        outputs = [marker],
        mnemonic = "ContainerImagePush",
        use_default_shell_env = True,
        execution_requirements = {"local": ""},
    )

    uri = ctx.actions.declare_file("{0}.uri".format(ctx.label.name))
    ctx.actions.run_shell(
        command = "echo -n $1/$2@$(cat $3) > $4",
        arguments = [
            ctx.actions.args().add_all([
                ctx.attr.container_push[PushInfo].registry,
                ctx.attr.container_push[PushInfo].repository,
                ctx.attr.container_push[PushInfo].digest,
                uri,
            ]),
        ],
        inputs = [ctx.attr.container_push[PushInfo].digest, marker],
        outputs = [uri],
        mnemonic = "PrintURI",
    )

    runfiles = ctx.runfiles(files = [uri])
    return [DefaultInfo(files = depset([uri]), runfiles = runfiles)]

container_push_at_build = rule(
    doc = """
      container_push is an executable rule. Building it produces an executable which pushes the
      image, but the executable is not run at build time. If you depend on a container_push target,
      it will only get built, but not run. container_push_at_build takes the output executable from
      container_push and runs it at build time.
    """,
    implementation = _container_push_at_build,
    attrs = {
        "container_push": attr.label(
            mandatory = True,
            providers = [PushInfo],
            executable = True,
            cfg = "host",
        ),
    },
    _skylark_testable = True,
)
