"""
The sematic_pipeline Bazel macro.
"""

load(
    "@io_bazel_rules_docker//python3:image.bzl",
    "py3_image",
    "repositories",
)
load("@io_bazel_rules_docker//container:push.bzl", "container_push")
load("@io_bazel_rules_docker//container:layer.bzl", "container_layer")
load("@io_bazel_rules_docker//container:image.bzl", "container_image")
load("@io_bazel_rules_docker//container:pull.bzl", "container_pull")
load("@rules_python//python:defs.bzl", "py_binary")

def sematic_pipeline(
        name,
        deps,
        registry,
        repository,
        data = None,
        base = "@sematic-worker-base//image",
        bases = None,
        env = None,
        dev = False):
    """
    A Bazel rule to run a Sematic pipeline.

    Invoking this target will package the entry point (<name>.py) and
    dependencies into a container image, register it to a remote registry, and
    execute the entry point.

    The `<name>_local` image skips all the container packaging and registration
    and simply runs the entry point.

    Args:
        name: name of the target

        deps: list of dependencies

        registry: URI of the container registry to use to register
            the container image

        repository: container repository for the image

        data: (optional) data files to add to the image

        base: (optional) label of the base image to use.

        bases: (optional)

        env: (optional) mapping of environment variables to set in the container

        dev: (optional) For Sematic dev only. switch between using worker in the installed
        wheel or in the current repo.
    """
    if bases == None:
        bases = {}
    if data == None:
        data = []

    if "default" not in bases:
        if base != None:
            bases["default"] = base
        else:
            fail("No default image specified. Set `base` or tag an image as default in `bases`.")
    elif bases["default"] != base:
        fail("default image is ambiguous, as base and bases['default'] were specified with different values")

    if dev:
        main = "@sematic//sematic/resolvers:worker.py"
        srcs = ["@sematic//sematic/resolvers:worker.py"]

        # note that this is only adding a script that wraps Ray
        # if it's there. It doesn't add an actual dependency on real
        # ray stuff.
        script_data = ["@sematic//bazel:ray", "@sematic//bazel:bazel_python"]
        py3_image_deps = deps + ["@sematic//sematic/resolvers:worker"]
    else:
        main = "@rules_sematic//:worker.py"
        srcs = ["@rules_sematic//:worker.py"]
        script_data = ["@rules_sematic//:ray", "@rules_sematic//:bazel_python"]
        py3_image_deps = deps

    image_uris = []
    push_rule_names = []

    for tag, base_image in bases.items():
        with_tools_image = "{}_{}_image_with_tools".format(name, tag)
        with_tools_layer = "{}_layer".format(with_tools_image)
        container_layer(
            name = with_tools_layer,
            files = script_data,
            directory = "/sematic/bin/",
        )
        container_image(
            name = with_tools_image,
            base = base_image,
            layers = [with_tools_layer],
        )
        env = env or {}

        # Leveraged by scripts in the image to determine
        # which python environment to use: the host python
        # env or the bazel-managed one.
        env["BAZEL_BUILT_IMAGE"] = "1"
        py3_image(
            name = "{}_{}_image".format(name, tag),
            main = main,
            srcs = srcs,
            data = data,
            deps = py3_image_deps,
            visibility = ["//visibility:public"],
            base = with_tools_image,
            env = env,
            tags = ["manual"],
        )

        push_rule_name = "{}_{}_push".format(name, tag)
        push_rule_names.append(push_rule_name)

        container_push(
            name = push_rule_name,
            image = "{}_{}_image".format(name, tag),
            registry = registry,
            repository = repository,
            tag = "{}_{}".format(name, tag),
            format = "Docker",
            tags = ["manual"],
        )

        uri_rule_name = "{}_{}_generate_image_uri".format(name, tag)
        image_uris.append(uri_rule_name)

        native.genrule(
            name = uri_rule_name,
            srcs = [":{}_{}_push.digest".format(name, tag)],
            outs = ["{}_{}_push_at_build.uri".format(name, tag)],
            cmd = "echo -n {}/{}@`cat $(location {}_{}_push.digest)` > $@".format(registry, repository, name, tag),
        )

    py_binary(
        name = "{}_binary".format(name),
        srcs = ["{}.py".format(name)],
        main = "{}.py".format(name),
        deps = deps,
        data = image_uris,
        tags = ["manual"],
    )

    py_binary(
        name = "{}_local".format(name),
        main = "{}.py".format(name),
        srcs = ["{}.py".format(name)],
        tags = ["manual"],
        deps = deps,
    )

    sematic_push_and_run(
        name = name,
        push_rule_names = push_rule_names,
    )

def base_images():
    repositories()

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
        digest = "sha256:e929213c8219562a48e82264569298e3ad79e97888e1e7521bd64587f37eceb3",
        registry = "index.docker.io",
        repository = "sematicai/sematic-worker-base",
        tag = "latest",
    )

    container_pull(
        name = "sematic-worker-cuda",
        digest = "sha256:bea3926876a3024c33fe08e0a6b2c0377a7eb600d7b3061a3f3f39d711152e3c",
        registry = "index.docker.io",
        repository = "sematicai/sematic-worker-base",
        tag = "cuda",
    )

def _sematic_push_and_run(ctx):
    script = ctx.actions.declare_file("{0}.sh".format(ctx.label.name))

    push_rule_runs = " && ".join([
        "\"$BAZEL_BIN\" run {}:{}".format(ctx.label.package, rule_name)
        for rule_name in ctx.attr.push_rule_names
    ])

    # the script it simple enough it doesn't really merit a template & template expansion
    script_lines = [
        "#!/bin/sh",

        # A common pattern is to have the bazel binary checked into the root of the
        # workspace. If that's present, use it instead of whatever is on the PATH.
        "test -f \"$BUILD_WORKSPACE_DIRECTORY/bazel\" && BAZEL_BIN=\"$BUILD_WORKSPACE_DIRECTORY/bazel\" || BAZEL_BIN=\"$(which bazel)\"",
        "if test -f \"$BAZEL_BIN\"; then",
        "\tcd $BUILD_WORKING_DIRECTORY",
        "\t{} && \"$BAZEL_BIN\" run {}_binary -- $@".format(push_rule_runs, ctx.label),
        "else",
        # Should probably not happen unless somebody has an exotic bazel setup.
        # At least make it clear what the problem is if it ever does happen.
        "\techo \"!!! bazel executable not found on PATH or in $BUILD_WORKSPACE_DIRECTORY !!!\"",
        "fi",
    ]
    command = "touch {}".format(script.path)
    for script_line in script_lines:
        command += " && echo '{}' >> {}".format(script_line, script.path)

    command = "{}".format(command)
    ctx.actions.run_shell(
        command = command,
        outputs = [script],
        mnemonic = "GenerateScript",
        use_default_shell_env = True,
        execution_requirements = {"local": "", "no-sandbox": "1"},
    )
    runfiles = ctx.runfiles(files = [script])

    return [DefaultInfo(files = depset([script]), runfiles = runfiles, executable = script)]

sematic_push_and_run = rule(
    doc = (
        """This rule should never be used directly, it is for internal Sematic use.

        It combines `bazel run //my_package:my_target_push` and
        `bazel run //my_package:my_target_binary` into a single `bazel run`-able target.
        """
    ),
    implementation = _sematic_push_and_run,
    attrs = {
        "push_rule_names": attr.string_list(
            doc = "List of push rules to execute",
            mandatory = True,
        ),
    },
    executable = True,
    _skylark_testable = True,
)
