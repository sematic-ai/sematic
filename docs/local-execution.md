Sematic lets you iterate on your pipeline locally before submitting it for
execution on a Kubernetes cluster in your cloud environment. Even locally, you
get some great Sematic perks such as the web dashboard, traceability, and
visualizations of artifacts.

To do so, select and pass an instance of the `LocalResolver` to your top-level
pipeline function's `resolve` method.

```python
pipeline(...).resolve(LocalResolver())
```

This will execute all steps of your pipeline on the machine where you issued the
above call, i.e. most typically on your local laptop, or dev machine on which
you are editing code.

## Metadata tracking

When using `LocalResolver`, pipeline and artifact metadata (e.g. pipeline graph,
execution status, artifact summaries, etc.) are persisted into the Sematic
server.

Whether the metadata is tracked and visualizable in a local server running on
your machine or a remote one deployed in your cloud environment is dictated by
the value of the `SEMATIC_API_ADDRESS` setting, which you can set using the following:

```shell
$ sematic set SEMATIC_API_ADDRESS https://address.to.deployed.server
```

By default, i.e. if you haven't set `SEMATIC_API_ADDRESS` to any value, metadata
will be tracked in a local server and database running on your local machine,
which can be started with:

```shell
$ sematic start
```

## Artifact storage

Where your pipeline's artifacts are being stored depends on how the API server
was configured. By default, when running locally after having launched the
server with `$ sematic start`, artifacts will be persisted on your local
machine, in the `~/.sematic/data` directory.

A different storage backend can be selected by selecting a different storage
plug-in when starting the server (whether a local or deployed server). For
example, to select the S3 storage plug-in:

```shell
$ STORAGE=sematic.plugins.storage.s3_storage.S3Storage AWS_S3_BUCKET=my-bucket sematic start
```