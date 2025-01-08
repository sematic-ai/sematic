# Sematic and Container Images

When Sematic runs your code in the cloud (in other words, when you are using
`CloudRunner`), it does so in a Docker container. Your code and all its
dependencies need to be in that Docker image for it to run.

Where does this Docker image come from? There are a few options, but a general
theme is that Sematic prefers to make the construction of the Docker image
transparent to you for simple cases, hooking into existing build tooling when
possible. However, we leave the flexibility to customize for advanced usages
if needed.

## Image Construction

Sematic currently supports two build systems:
- the [Native Docker Build System](#docker)
- the [Bazel Build System](#bazel)

### Docker

{% hint style="warning" %}
The Native Docker Build System only supports Debian GNU/Linux.
{% endhint %}

{% hint style="warning" %}
The Native Docker Build System does not support multiple base images.
{% endhint %}

If you don't want to use [Bazel](https://bazel.build) to manage your project,
you can build container images to execute workloads in the cloud using
Sematic's Native Docker Build System. You can configure how to package your
source code, dependencies, and data in a container image. A complete example of
this hookup can be found in our
[Docker example repo](https://github.com/sematic-ai/example_docker), but here's
a summary of the steps.

#### Configuration

In order to configure building the container image for a specific launch
script, you need to create a configuration file in the same directory as the
script, which has the same name as it does, only the ".yaml" extension instead
of the ".py" extension. The configuration file must have the following syntax:

```yaml
version: <version>
base_uri: <base image URI>
image_script: <custom image URI script path>
build:
    platform: <optional docker platform>
    requirements: <optional requirements file path>
    data: <optional list of data file globs>
    src: <optional list of source file globs>
push:
    registry: <image push registry>
    repository: <image push repository>
    tag_suffix: <optional image push tag suffix>
docker:
    <optional docker-py configuration arguments>
```

- `version` is an integer that specifies the version of the syntax the file
  contents adheres to. The latest schema version is `1`.
- `base_uri` is a string that specifies the base image to use for constructing
  the final container image. It must have the `<repository>:<tag>@<digest>`
  format. The base image must be Debian GNU/Linux-based, and have a `python3`
  binary installed. Exactly one of `base_uri` and `image_script` must be
  specified.
- `image_script` is a string that specifies the path to an executable script
  which must output the URI of the base image to use for constructing the final
  container image to standard output. This URI must have the
  `<repository>:<tag>@<digest>` format. This script can output anything to
  standard error. The intent is to allow the construction of the base image
  dynamically instead of specifying a static base image URI. The base image
  must be Debian GNU/Linux-based, and have a `python3` binary installed.
  Exactly one of `base_uri` and `image_script` must be specified.
- `build` is an optional section that describes how to compose the image.
- `build.platform` is an optional string that specifies what
  [platform](https://docs.docker.com/build/building/multi-platform/) to build
  the image for.
- `build.requirements` is an optional string that specifies the path to a
  requirements file to install in the image via `pip`. The requirements file
  may refer to wheels specified in the `build.data` configuration.
- `build.data` is an optional list of strings that specifies globs that will be
  resolved to data files to copy directly to the image.
- `build.src` is an optional list of strings that specifies globs that will be
  resolved to source files to copy directly to the image.
- `push` is an optional section that describes how to push the image to a
  repository. A valid case to skip this section is if the Docker Server you are
  using is the same registry that is also used to source cloud images from. If
  this section is specified, then `push.registry` and `push.repository` must
  both be specified.
- `push.registry` is a string that specifies the registry where to push the
  resulting image. The intent is to have this registry accessible by a Sematic
  Server which will spin up worker containers using the image.
- `push.repository` is a string that specifies the repository inside the
  `push.registry` to use.
- `push.tag_suffix` is an optional string that specifies a suffix to add at the
  end of an automatically-generated tag for the resulting image.
- `docker` is an optional section that configures the `docker-py` client used
  internally to build the image. The full list of configurations can be found
  [here](https://docker-py.readthedocs.io/en/stable/client.html#docker.client.DockerClient).

##### Execution

To execute the launch script, the `sematic run` command is used:

```bash
$ sematic run --help
Usage: sematic run [OPTIONS] SCRIPT_PATH [SCRIPT_ARGUMENTS]...

Options:
  -b, --build           Build a container image that will be used to execute
                        the pipeline, using the configured build plugin.
                        Defaults to `False`. If not set, the pipeline will be
                        run locally in the current environment.
  -n, --no-cache        When `--build` is specified, builds the image from
                        scratch, ignoring previous versions. Defaults to
                        `False`.
  -l, --log-level TEXT  The log level to use for building and launching the
                        pipeline. Defaults to `INFO`.
  --help                Show this message and exit.
```

For example, if the launch script which uses
[CloudRunner](./cloud-runner.md) is `path/to/my/hello_world.py`, then we can
use this `path/to/my/hello_world.yaml` build configuration file:

```yaml
version: 1
base_uri: "sematicai/sematic-worker-base:latest@sha256:bea3926876a3024c33fe08e0a6b2c0377a7eb600d7b3061a3f3f39d711152e3c"
build:
  src: ["hello_world.py"]
push:
  registry: my_registry
  repository: my_repo
```

And execute it in the cloud with:

```bash
$ sematic run --build path/to/my/hello_world.py
```

Omitting the `--build` flag results in skipping the entire build process, with
the entire pipeline being executed locally. Only using
[LocalRunner or SilentRunner](https://docs.sematic.dev/diving-deeper/concepts#runners)
makes sense in this context.

Building the image uses layer caching for temporal and spatial optimization. If
you find that you have an image with stale layers that, for example, have an
older version of a library installed, then you can deactivate the caching and
force a complete rebuild of the image by passing the `--no-cache` flag:

```bash
$ sematic run --build --no-cache path/to/my/hello_world.py
```

{% hint style="warning" %}
The launch script is executed locally, using the local Python installation.
This means all dependencies that the launch script imports must be installed in
the environment. Dependencies used exclusively by the pipeline Functions which
execute inside the containers do not need to be installed in the user's
environment.
{% endhint %}

##### Configuration file overloading

In addition to the launch script-specific build configuration file, reusable
build configuration files named `sematic_build.yaml` can be specified along the
directory path, starting from the project root (the directory in which the
`sematic run` command is issued), and traversing down to the launch script's
directory.

These build configuration file are loaded in the described order, and their
individual configuration values accumulated if they are lists, and overwritten
if they are not. This way, common configuration values can be specified once
and shared between different launch scripts.

In the example below, the configuration for `my_script1.py` will be constructed
from `my_project/sematic_build.yaml`, and from
`my_project/subdir1/my_script1.yaml`. The configuration for `my_script2.py`
will be constructed from `my_project/sematic_build.yaml`,
`my_project/subdir1/subdir2/sematic_build.yaml`, and from
`my_project/subdir1/subdir2/my_script2.yaml`.

```
my_project
├── sematic_build.yaml
└── subdir1
    ├── my_script1.yaml
    ├── my_script1.py
    └── subdir2
        ├── sematic_build.yaml
        ├── my_script2.yaml
        └── my_script2.py
```

##### File paths

All files referenced in the build configuration must be enclosed inside the same
project, for security reasons. You cannot reference files outside the project
root, meaning the directory from which you execute `sematic run`. As a
consequence, referencing absolute paths in the build configuration files is not
permitted.

Relative file paths will always be resolved from the parent directory of the
build configuration file itself.

Project-relative paths can be specified by prefixing the path with `//`.

In the example below, both of these configuration values would correctly
reference the two data files inside `my_script.yaml` (they can be mixed and
matched):
- `data: ["//data1.txt", "//subdir/data2.txt"]`
- `data: ["../data1.txt", "data2.txt"]`

```
my_project
├── data1.txt
└── subdir
    ├── my_script.yaml
    ├── my_script.py
    └── data2.txt
```

##### Requirements files

In order to package third party dependencies (code that is not present in
`Python` builtins or inside your pipeline project), you can specify them in a
[requirements.txt file](https://pip.pypa.io/en/stable/reference/requirements-file-format/).
When referenced in the build configuration, this file will be copied to the
image, and `pip` installed. Then the packages it lists will be available for
import at runtime. Local wheel files listed in the `data` section are also
referenceable in the requirements file.

For example, if we have the following `requirements.txt` file:

```
foo
bar==42
baz.whl
```

and the following `launch_script.yaml` file:

```yaml
version: 1
base_uri: "sematicai/sematic-worker-base:latest@sha256:bea3926876a3024c33fe08e0a6b2c0377a7eb600d7b3061a3f3f39d711152e3c"
build:
  requirements: "requirements.txt"
  data: ["baz.whl"]
  src: ["launch_script.py", "pipeline.py"]
push:
  registry: my_registry
  repository: my_repo
```

then the resulting image will have the `foo` and `bar` installed from
[`PyPi`](https://pypi.org/), with `bar` guaranteed to have version `42`, and
`baz` installed from the local `baz.whl` wheel file.

If `launch_script.py` launches a pipeline contained in `pipeline.py`, then
`pipeline.py` can safely import the `foo`, `bar`, and `baz` modules, as they
will be available in the container image that will execute the workload in the
cloud. Because `launch_script.py` is executed locally, if it imports any of
those modules, it is up to the use to ensure their environment has them
installed.

##### Build workflow

For example, when running
`sematic run --build path/to/my/launch_script.py -- my_arg1 my_arg2`:

1. Starting from the current directory, the path is traversed down to
   `path/to/my/`, and files named `sematic_build.yaml` and identified and
   loaded in order, overwriting non-collection configuration values, and
   extending collection configuration values.
2. If a file named `path/to/my/launch_script.yaml` exists, it is also loaded in
   the same manner.
3. If the resulting configuration has an `image_script` configuration value
   set, then this script is executed, and the image identified by the URI it
   outputs is used as a base image. Alternatively, if the `base_uri`
   configuration value is set, then the image it identifies is used as a base
   image.
4. If the resulting configuration has a `docker` section, then a
   [`docker-py` client](https://docker-py.readthedocs.io/en/stable/client.html#docker.client.DockerClient)
   is instantiated using those configurations. If not, one is instantiated
   using default configurations from the local environment.
5. If the resulting configuration has a `build` section, then:
   1. The `data` file globs are resolved and copied to the image, if any.
   2. The `requirements` file is copied to the image and `pip` installed, if
      any. Any wheels included in `data` can also be referenced and installed.
   3. The `src` file globs are resolved and copied to the image, if any. If no
      source files are specified, and if the base image is specified via
      `base_uri` (which cannot produce a dynamic image like `image_script` and
      therefore cannot account for source code changes), then the launch script
      is automatically copied to the image, to cover cases where this script
      contains the entire pipeline.
   4. If `sematic` itself is not present in the image at this point, it is
      `pip` installed.
   5. The image is built for the specified `platform`(s), if any.
6. If the resulting configuration has a `push` section, then the image is
   pushed to the specified `repository` and `repo`, using an
   automatically-generated tag, which is suffixed with the specified
   `tag_suffix`, if any. Therefore, the configured Docker client must have
   permissions to create / push images to both the "local" and "remote"
   registries.
7. The `path/to/my/launch_script.py` is executed locally with the `my_arg1` and
   `my_arg2` arguments, and with the `"SEMATIC_CONTAINER_IMAGE"` environment
   variable set to the remote image URI, if pushing was configured, or to the
   local image URI, if it was not. This way, the `Runner` will instruct the
   Sematic Server to use the image for cloud workloads.

#### Custom base images with Docker

As stated, and similarly to the Bazel Build System, custom base images can be
specified via the `base_uri` configuration values or by executing the
configured `image_script`.

#### Totally Custom Images with Docker

If a `build` section is not specified in the build configuration, then source
code or data files will not be explicitly copied to the image. the base image
specified through `base_uri`, or obtained by executing the `image_script` will
roughly be used as the image fow workloads in the cloud, so they must already
contain all code and data dependencies.

### Bazel

{% hint style="info" %}
Although Bazel does not officially support RPM Linux distributions such as
RedHat, CentOS, and Fedora, they endorse an
[unofficial solution](https://bazel.build/install/redhat).
{% endhint %}

[**Bazel**](https://bazel.build) is a Dependency Package Manager and Build
System. When executing your code, it can package your source code, its
dependencies, data, and a custom version of Python in a sandbox container which
is built natively, without using
[Docker](https://docs.docker.com/get-started/overview/). This same image can
then be used to execute pipeline
[Functions](https://docs.sematic.dev/diving-deeper/concepts#sematic-functions)
in the cloud.

If you're using Bazel, having Sematic create a cloud image containing your code
is quite straightforward: we have a Bazel macro that will allow you to create
targets for building and pushing your image at the same time as creating a
target to run the code locally. A complete example of this hookup can be found
in our [Bazel example repo](https://github.com/sematic-ai/example_bazel), but
here's a summary of the steps. This assumes you already have a Python Bazel
target to run a Sematic pipeline (we'll refer to the Python script for this
target your "launch script").

1. Include Sematic's GitHub repo as a Bazel repository in your Bazel
   `WORKSPACE` file:
    ```
    git_repository(
        name = "rules_sematic",
        branch = "main",
        remote = "git@github.com:sematic-ai/sematic.git",
        strip_prefix = "bazel",
    )
    ```

2. Load Sematic's base images in your `WORKSPACE` file, using, for example:
    ```starlark
    load("@rules_sematic//:pipeline.bzl", "base_images")
    base_images()
    ```

3. Ensure you have a container registry where you can push your Docker images
   to.

4. In the Bazel `BUILD` file where you have defined your launch script, load
   Sematic's pipeline macro:
   `load("@rules_sematic//:pipeline.bzl", "sematic_pipeline")`.

5. Replace the Python binary target for your launch script with
   `sematic_pipeline`, using the same `deps` as you use for the binary target.

6. Fill out the `registry` and `repository` fields of the `sematic_pipeline`
   with information about where to push your image.

When you're done, your project's `WORKSPACE` file should look something like:

```starlark
# Bazel WORKSPACE file

# rules_python archive and toolchain

# io_bazel_rules_docker archive

load(
    "@io_bazel_rules_docker//repositories:repositories.bzl",
    "repositories",
)

repositories()

## SEMATIC RULES

load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")

git_repository(
    name = "rules_sematic",
    branch = "main",
    remote = "git@github.com:sematic-ai/sematic.git",
    strip_prefix = "bazel",
)

load("@rules_sematic//:pipeline.bzl", "base_images")

base_images()

```

Your package's `BUILD` file should look something like:

```starlark
# BUILD file at path/to/pipeline

load("@rules_sematic//:pipeline.bzl", "sematic_pipeline")
load(
    "@rules_python//python:defs.bzl",
    "py_library",
)
load("@<your-dependency-repo>//:requirements.bzl", "requirement")

py_library(
    name = "main_lib",
    srcs = [
        "main.py",
        "pipeline.py",
        ...
    ],
    deps = [
        requirement("sematic"),
        ...
    ],
)

sematic_pipeline(
    name = "main",  # if the launch script of your pipeline is main.py
    registry = "<container-registry-uri>",
    repository = "<container-repository>",
    deps = [
        ":main_lib",
    ],
    # Optional base image to use
    base = "<base-image>",
    # Optional environment variables to set in the image
    env = {"VAR": "VALUE"}
)
```

The non-builtin Python dependencies listed in the `deps` field must also be
listed in a `requirements.txt` file that must be present in the same directory
as the `BUILD` file.

With that, you're done! Assuming the target for your launch script was
`//my_repo/my_package:my_target`, you now have the following targets available:

- `$ bazel run //my_repo/my_package:my_target`: still runs your target, but
  builds and pushes a Docker image with your code and its dependencies first.
  It's essentially an alias for
  `$ bazel run //my_repo/my_package:my_target_default_push`, followed by
  `$ bazel run //my_repo/my_package:my_target_binary`.
- `$ bazel run //my_repo/my_package:my_target_binary`: builds the image, does
  NOT push it, and executes your launch script. Generally this is only useful
  when combined with `$ bazel run //my_repo/my_package:my_target_default_push`.
- `$ bazel run //my_repo/my_package:my_target_local`: runs your target WITHOUT
  building and pushing the image. This can help for local development when you
  don't want the overhead of waiting for the build & push. Differs from
  `:my_target_binary` in that Sematic will not know how to reference a
  container image when executed this way, and thus won't work for remote
  execution even when combined with `:my_target_default_push`.
- `$ bazel run //my_repo/my_package:my_target_default_image`: builds the image,
  but doesn't push it, or run your script.
- `$ bazel run //my_repo/my_package:my_target_default_push`: builds and pushes
  the image, but doesn't run your script.

#### Custom base images with Bazel

The `sematic_pipeline` macro also allows you to specify a custom base image to
cover any dependencies you have that aren't specified in Bazel. You can do this
by setting the `base` field of the `sematic_pipeline` macro:

```starlark
sematic_pipeline(
    name = "my_pipeline",
    base = "uri://to/my/base/image",
    ...
)
```

If, for example, your Bazel setup assumes that it is running on a machine with a
particular version of Cuda, you can bake that into the base image, but let
Sematic's Bazel hook handle all the Python and other native code you want in
the image. Sematic also provides a couple base images out-of-the-box, which can
be referenced as `"@sematic-worker-base//image"` and
`"@sematic-worker-cuda//image"` in Bazel. `sematic-worker-cuda` includes
Python 3.9 and an installation of `cuda`, and is actually the base image used by
default when you use the `sematic_pipeline` macro. `sematic-worker-base` is the
same, but doesn't include cuda (this is helpful if you want a lighter image and
don't use GPUs in your pipeline).

If you like, you can also specify another base image not provided by Sematic.
There are a few requirements on this image though, so be sure to read through
the ["Totally Custom Images with Bazel"](#totally-custom-images-with-bazel)
section below to understand what those are. Note that if you are using Bazel,
requirements 1, 2 & 3 from that section will already be taken care of.

#### Totally Custom Images with Bazel

If you want full control over how your Docker image is produced, Sematic
provides a hook to make that possible. Just set the `SEMATIC_CONTAINER_IMAGE`
environment variable to the URI for the Docker image you want your pipeline to
use. There are some requirements on this image though:

1. It must contain your source code and its dependencies
2. It must be pushed to a container registry that can be accessed by the cluster
   where your code is going to run in the cloud
3. The entrypoint must be set to a script which executes
   `/usr/bin/python3 -m sematic.resolvers.worker "$@"`
4. `/usr/bin/python3` must be a valid Python interpreter in the image
5. The home directory inside the image must be writable
6. The `/sematic/bin/` directory inside the image must be writable
7. `/sematic/bin` must be on your `PATH`

#### Multiple base images with Bazel

Please see [Support for multiple images](./multiple-base-images.md).

## Working with images programmatically

When launching Sematic pipelines, there is always a Python script that submits
the job (either for local execution or for execution in the cloud). We refer to
this as the "launch script." You may want to have your launch script behave
differently depending on whether a suitable cloud image is available. Sematic
has provided `sematic.has_container_image` to enable this use case. A common
pattern is to determine which `Runner` to use based on the result of this
function:

```python
from sematic import has_container_image, CloudRunner

from my_package import my_pipeline

runner = CloudRunner() if has_container_image() else None
runner.run(my_pipeline())
```
