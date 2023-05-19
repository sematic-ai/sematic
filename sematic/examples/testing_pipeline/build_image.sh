#!/usr/bin/env bash
set -e

# build the image
# use the project root as the work directory; the Dockerfile uses project-relative paths
docker build \
    --platform linux/amd64 \
    --tag testing_pipeline:default_main \
    -f Dockerfile ../../../ 1>&2

# output the URI in the required format
digest=`docker inspect --format='{{.Id}}' testing_pipeline:default_main`
echo "testing_pipeline:default_main@${digest}"
