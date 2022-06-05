load(
    "@io_bazel_rules_docker//python3:image.bzl",
    "py3_image"
)

glow_py_lib(
    name = "app",
    srcs = ["app.py"],
    deps = [
        requirement("flask"),
        requirement("flask-cors"),
    ]
)

glow_py_lib(
    name = "server_lib",
    srcs = ["server.py"],
    data = ["//glow/ui:ui_build"],
    deps = [
        "//glow:config",
        "//glow/api:app",
        "//glow/api/endpoints:runs",
        "//glow/api/endpoints:artifacts",
        "//glow/api/endpoints:edges",
        requirement("flask"),
        requirement("flask-socketio"),
        requirement("eventlet")
    ]
)

py_binary(
    name = "server",
    main = "server.py",
    srcs = ["server.py"],
    deps = [
        ":server_lib",
    ]
)

#container_image(
#    name = "server_image",
    # References container_pull from WORKSPACE (above)
#    base = "@py3_image_base//image",
#    files = ["//java/com/example/app:Hello_deploy.jar"],
#    cmd = ["Hello_deploy.jar"]
#)

py3_image(
    name = "server_image",
    srcs = ["server.py"],
    deps = [":server_lib"],
    main = "server.py",
)

#app_layer(
#        name = "server_image",
#        base = "@py3_image_base//image",
#        entrypoint = ["/usr/bin/python"],
        #env = env,
#        binary = "server",
        #visibility = visibility,
        #tags = tags,
        #args = kwargs.get("args"),
        #data = kwargs.get("data"),
        #testonly = kwargs.get("testonly"),
        # The targets of the symlinks in the symlink layers are relative to the
        # workspace directory under the app directory. Thus, create an empty
        # workspace directory to ensure the symlinks are valid. See
        # https://github.com/bazelbuild/rules_docker/issues/161 for details.
        #create_empty_workspace_dir = True,
#    )