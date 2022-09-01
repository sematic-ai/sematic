# Sematic and Docker Images

When Sematic runs your code in the cloud, it does so in a Docker container.
Your code and all its dependencies need to be in that Docker image for it
to run. Where does this Docker image come from? There are a few options, but
a general theme is that Sematic prefers to make the construction of the Docker
image transparent to you for simple cases, hooking into existing build tooling
when possible. However, we leave the flexibility to customize for advanced
usages if needed.

## Image Construction
### Bazel
If you're using bazel, having Sematic create a cloud image containing your code
is quite straightforward: we have a bazel macro that will allow you to create
targets for building and pushing your image at the same time as creating a target
to run the code locally. A complete example of this hookup can be found in our
[bazel example repo](https://github.com/sematic-ai/example_bazel), but here's a
summary of the steps. This assumes you already have a python bazel target to run
a Sematic pipeline (we'll refer to the python script for this target your
"launch script").

1. Include Sematic's GitHub repo as a bazel repository in your bazel WORKSPACE
2. Load Sematic's base images in your WORKSPACE, using, for example
`load("@rules_sematic//:pipeline.bzl", "base_images")`
3. Ensure you have a container registry where you can push your Docker images
to
4. In the bazel `BUILD` file where you have defined your launch script, load
Sematic's pipeline macro:
`load("@rules_sematic//:pipeline.bzl", "sematic_pipeline")`
5. Replace the python binary target for your launch script with
`sematic_pipeline`, using the same `deps` as you use for the binary target
6. Fill out the `registry` and `repository` fields of the `sematic_pipeline`
with information about where to push your image.

With that, you're done! Assuming the target for your launch script was
`//my_repo/my_package:my_target`, you now have the following targets available:

- `//my_repo/my_package:my_target`: still runs your target, but builds a Docker
image with your code and its dependencies first
- `//my_repo/my_package:my_target_local`: runs your target WITHOUT building and
pushing the image. This can help for local development when you don't want the
overhead of waiting for the build & push.
- `//my_repo/my_package:my_target_image`: builds the image, but doesn't push it
or run your script
- `//my_repo/my_package:my_target_push`: builds and pushes the image, but
doesn't run your script

#### Custom base images
The `sematic_pipeline` macro also allows you to specify a custom base image to
cover any dependencies you have that aren't specified in bazel. You can do this
by setting the `base` field of the `sematic_pipeline` macro, If, for
example, your bazel setup assumes that it is running on a machine with a
particular version of Cuda, you can bake that into the base image but let
Sematic's bazel hookup handle all the python and other native code you want in
the image. Sematic also provides a couple base images out-of-the-box, which can
be referenced as `"@sematic-worker-base//image"` and
`"@sematic-worker-cuda//image"` in bazel. `sematic-worker-cuda` includes
python 3.9 and an installation of cuda, and is actually the base image used by
default when you use the `sematic_pipeline` macro. `sematic-worker-base` is the
same, but doesn't include cuda (this is helpful if you want a lighter image and
don't use GPUs in your pipeline).

If you like, you can also specify another base image not provided by Sematic.
There are a few requirements on this image though, so be sure to read through
the ["Totally Custom Image"](#totally-custom-image) section below to understand
what those are. Note that if you are using bazel, requirements 1 & 2 from that
section will already be taken care of.

### requirements.txt
Coming soon!

### Totally Custom Image
If you want full control over how your Docker image is produced, Sematic
provides a hook to make that possible. Just set the `SEMATIC_CONTAINER_IMAGE`
environment variable to the URI for the Docker image you want your pipeline to
use. There are some requirements on this image though:

1. It must contain your source code and its dependencies
2. It must be pushed to a container registry that can be accessed by the cluster
where your code is going to run in the cloud
3. `/usr/bin/python3` must be a valid python interpreter in the image
4. The home directory inside the image must be writable

## Working with images
When launching Sematic pipelines, there is always a python script that submits
the job (either for local exection or execution in the cloud). We refer to this
as the "launch script." You may want to have your launch script behave
differently depending on whether a suitable cloud image is available. Sematic
has provided `sematic.has_cloud_image` to enable this use case. A common pattern
is to determine which resolver to use based on the result of this function:

```python
from sematic import has_cloud_image, CloudResolver

from my_package import my_pipeline

resolver = CloudResolver() if has_cloud_image() else None
my_pipeline().resolve(resolver)
```