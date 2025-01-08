# Sematic Testing Pipeline

This is the Sematic Testing Pipeline. It is used to test the behavior of the Server and of the Runner.
The arguments control the shape of the pipeline, as described in the individual help strings. Some of
the arguments have dependencies on other arguments, and missing values will be reported to the user.
At the end of the pipeline execution, the individual future outputs are collected in a future list and
reduced.

## Running

After updating [main.yaml](./__main__.yaml) with your own registry and repository,
you can launch the pipeline with:

```bash
$ sematic run --build sematic/examples/testing_pipeline/__main__.py -- --cloud
```
