## Can I have multiple images in one pipeline?

In Sematic, every step in a pipeline execution uses the same container image.
Some steps might leverage different libraries than others, so you may wonder
if it might make sense to have different images for different steps in the
pipeline. You might hope that lighter steps could run with a lighter image and
speed up the time to start the container for them. However, there are more good
reasons to put everything in one image than to separate them:

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
- If you have a step which is really lightweight, there's a better option than having
  a small new container: _no_ new container. This is a great case for inline functions.
  See the [execution mode docs](https://docs.sematic.dev/execution-modes) for more.
