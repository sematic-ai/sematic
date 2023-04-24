## Support for multiple images

### Prefer a single image

In Sematic, by default every step in a pipeline executes within the same
container image. Some steps might leverage different libraries than others, so
you may wonder if it might make sense to have different images for different
steps in the pipeline. You might hope that lighter steps could run with a
lighter image and speed up the time to start the container for them. However,
there are more good reasons to put everything in one image than to separate
them:

- It can actually speed up container download to re-use the same image, as Kubernetes
  nodes will only download the image once and have it cached for re-use in other steps in
  the pipeline.
- It can quickly become tricky to remember what dependencies are going to be available
  in which step. When you have a single python interpreter executing all your code, all
  the dependencies are available everywhere. We want to bring this intuitive experience
  to the cloud.
- With different images for different steps comes the potential for variations in what
  versions of libraries are available in which step. For example, if `step_1` returns a
  Scikit-learn model using `scikit-learn==1.1.2`, you'll want to be sure that `step_2`
  isn't trying to use that model with `scikit-learn==0.24.2`
- Image builds are slow, and slow down the iteration loop of change code, push image,
  execute. Sematic aims to make this loop as tight as possible, and having to build multiple
  images every time (or remember which ones you need to rebuild when) would significantly
  damage this workflow.
- If you have a step which is really lightweight, there's a better option than
  having a small new container: _no_ new container. This is a great case for
  [Inline Functions](./glossary.md#standalone-inline-function). See the
  [CloudResolver docs](cloud-resolver.md#when-to-use-inline) for more.

### Multiple images if you must

There are cases where step-specific images can be warranted. For example one
step uses a third-party library that comes packaged as a container image.

For this reason, Sematic enables specifying multiple **base** images. This means
that Sematic will use these different images as bases on top of which your
pipeline code will be packaged to make sure the necessary code and dependencies
are available at runtime. Sematic will also override the entry point of the
image with the standard Sematic worker entry point.

The API to specify a **single** base image for all your pipeline is as follows in your pipeline's Bazel `BUILD` file:

```starlark
load("@rules_sematic//:pipeline.bzl", "sematic_pipeline")

sematic_pipeline(
  name="main",
  registry = "your.image.registry",
  repository = "image-repo",
  base = "@your-image-target",
  deps = [...],
)
```

To specify different base images for different steps remove the `base` argument and instead pass a mapping to the `bases` argument:

```starlark
sematic_pipeline(
  name="main",
  ...
  bases={
    "cuda": "@cuda-base-target"
  }
)
```
Then in your pipeline code, specify which image to use by passing the
corresponding key to the Sematic decorator:

```python
@sematic.func(base_image_tag="cuda")
def train_model(...):
  ...
```

Then, an image built on top of `@cuda-base-target` is used to execute this particular function.

Notes:

- Nested functions (i.e. if `train_model` calls other Sematic functions), will
  execute according to their own settings, i.e. with the default image unless
  otherwise specified.
- A default base image to be used for all steps where no `base_image_tag` is
  passed can be specified either by setting the `base` argument like in the
  single image case above, or setting an image target with the `"default"` key
  to `bases`.
