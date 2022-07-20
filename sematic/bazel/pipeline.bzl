load(
    "@io_bazel_rules_docker//python3:image.bzl",
    "py3_image",
)
load("@io_bazel_rules_docker//container:push.bzl", "container_push")
load("@rules_python//python:defs.bzl", "py_binary")
load("@io_bazel_rules_docker//container:providers.bzl", "PushInfo")
load("@io_bazel_rules_docker//container:pull.bzl", "container_pull")
load("@rules_python//python:pip.bzl", "pip_install")
load("@python3_9//:defs.bzl", "interpreter")

def sematic_pipeline(
        name,
        deps,
        registry,
        repository = None,
        data = None,
        base = "@sematic-worker-base//image",
        env = None):
    """docstring"""
    py3_image(
        name = "{}_image".format(name),
        main = "@sematic//sematic/resolvers:worker.py",
        srcs = ["@sematic//sematic/resolvers:worker.py"],
        data = data,
        deps = deps + ["@sematic//sematic/resolvers:worker"],
        visibility = ["//visibility:public"],
        base = base,
        env = env or {},
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
        srcs = ["{}.py".format(name)],
        deps = deps,
        data = [":{}_push_at_build".format(name)],
        tags = ["manual"],
    )

    py_binary(
        name = "{}_local".format(name),
        main = "{}.py".format(name),
        srcs = ["{}.py".format(name)],
        tags = ["manual"],
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

def base_images():
    container_pull(
        name = "python_39",
        digest = "sha256:4169ae884e9e7d9bd6d005d82fc8682e7d34b7b962ee7c2ad59c42480657cb1d",
        registry = "index.docker.io",
        repository = "python",
        # tag field is ignored since digest is set
        tag = "3.9-slim-bullseye",
    )

    container_pull(
        name = "sematic-worker-base",
        digest = "sha256:d0c0e15f4f20dc60e844523a012c9cc927acbd4c5187b943a4a4a90b0ed70eee",
        registry = "index.docker.io",
        repository = "sematicai/sematic-worker-base",
        tag = "latest",
    )

    container_pull(
        name = "sematic-worker-cuda",
        digest = "sha256:6cbedeffdbf8ef0e5182819b4ae05a12972f61a4cd862fe41e4b3aaca01888da",
        registry = "index.docker.io",
        repository = "sematicai/sematic-worker-base",
        tag = "cuda",
    )
