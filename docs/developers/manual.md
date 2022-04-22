# Developer manual

## Add third-party pip dependency

Add dependency to `requirements/requirements.in`, and if possible, set a fixed version.

Then run:
```shell
$ python3 -m piptools compile requirements/requirements.in > requirements/requirements.txt --allow-unsafe
```

`--allow-unsafe` is to ensure `setuptools` doesn't get filtered out.

## Build the glow wheel

```shell
$ bazel build //glow/glow_wheel
```