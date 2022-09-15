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
we are ready to push the release.

```
make test-release
make release
```

Once you have pushed it to PyPi, add the git tag

```
RELEASE_VERSION=v$(python3 ./sematic/versions.py)
git tag $RELEASE_VERSION
git push --tags
```

Next, build and push the server image. Use the dockerfile at
`docker/Dockerfile.server`. Use the wheel you built before in the directory
you run.
```
$ cd docker
$ RELEASE_VERSION=v$(python3 ../sematic/versions.py)
$ docker build -t "sematicai/sematic-server:$RELEASE_VERSION" -f Dockerfile.server .
$ docker push "sematicai/sematic-server:$RELEASE_VERSION"
```

Finally, draft the release on GitHub.