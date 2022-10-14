# Developer Docs
This directory contains documentation for people working on/developing Sematic
itself. Documents intended for users of Sematic are in the `docs` directory,
and are published to https://docs.sematic.dev/

## Setup

The developer tools need to be installed by running this command once (and subsequently whenever
`requirements/ci-requirements.txt`) will be updated:
```bash
$ pip3 install -r requirements/ci-requirements.txt
```

## Releasing
**Note:** Actually pushing the released wheel can only be done if you have
access to the PyPi repo, which is limited to employees of Sematic.

- Bump the version in `wheel_version.bzl`, `sematic/versions.py`,
  and `helm/sematic/values.yaml`
- Update `changelog.md` with the new version number
- Build the UI:
```bash
$ make ui
```
- Build the wheel:
```bash
$ make wheel
```
- copy wheel from `bazel-bin/sematic/sematic-....whl` into a scratch directory,
and use a virtual env to test:

```bash
$ pip3 install <wheel path>
$ sematic start
$ sematic run examples/mnist/pytorch
```

Do this for all supported versions of python. You can check your virtual env Server and
Python versions using `sematic version`.
If everything works fine, we are ready to push the release.

```bash
$ make test-release
$ make release
```

Once you have pushed it to PyPi, add the git tag

```bash
$ export RELEASE_VERSION=v$(python3 ./sematic/versions.py)
$ git tag $RELEASE_VERSION
$ git push origin $RELEASE_VERSION
```

Next, build and push the server image. Use the dockerfile at
`docker/Dockerfile.server`. Copy the wheel you built before in the directory
you run.
```bash
$ cd docker
$ export RELEASE_VERSION=v$(python3 ../sematic/versions.py)
$ docker build -t "sematicai/sematic-server:$RELEASE_VERSION" -f Dockerfile.server .
$ docker push "sematicai/sematic-server:$RELEASE_VERSION"
```

Finally, draft the release on GitHub. Add a "What's Changed" section, a "Full Changelog" link,
and attach the wheel in the assets section.
