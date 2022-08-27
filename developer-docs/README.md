# Developer Docs
This directory contains documentation for people working on/developing Sematic
itself. Documents intended for users of Sematic are in the `docs` directory,
and are published to https://docs.sematic.dev/

## Releasing
**Note:** Actually pushing the released wheel can only be done if you have
access to the PyPi repo, which is limited to employees of Sematic.

- Bump the version in `wheel_version.bzl` and `sematic/versions.py`
- Update `changelog.md` with the new version number
- `make ui`
- `make wheel`
- copy wheel from `bazel-bin/sematic/sematic-....whl` into a scratch directory,
and use a virtual env to test:

```
pip install sematic
sematic start
sematic run examples/mnist/pytorch
```

Do this for all supported versions of python. If everything works fine,
we are ready to push the release. Once you have pushed it to PyPi,
```
git tag vMAJOR.MINOR.PATCH
git push --tags
```
