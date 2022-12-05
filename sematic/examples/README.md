This module contains simple example pipelines which showcase certain features,
which you can use to get familiarized with the framework, or try out things.

You can run these examples using the Sematic CLI:
```bash
$ sematic run examples/add
```

Examples are shorthand simple pipelines declared using the `sematic_pipeline`
Bazel rule, which expects a `__main__.py` file as the execution entry point.
They can only be executed locally. For cloud execution, you will need to
declare your own entry points which invoke resolution using `CloudResolver`.

In order to write your own pipeline (an example pipeline, or a more complex
pipeline), you can quickly clone the entire required file structure from the
`template/` directory using:
```bash
$ sematic new --from examples/template /my/pipeline/path/dir
```
