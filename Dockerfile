# Dockerfile for the API server
# Ideally we would do this via Bazel instead but the py3_image rules
# are currently broken for M1 Macs

# see https://stackoverflow.com/questions/65612411/forcing-docker-to-use-linux-amd64-platform-by-default-on-macos/69636473#69636473
# for why --platform
FROM --platform=linux/amd64 python:3.9-bullseye

RUN python3 -m pip install --upgrade pip

# `make build_server_image` copies the build wheel to the root of the repo
COPY /sematic_server-0.0.1-py3-none-any.whl /


# RUN pip install sematic_server-0.0.1-py3-none-any.whl
# Not pip install because of multiple dist-info directories
# Because Bazel's py_wheel bundles all dependencies
# TODO: Fix this
RUN unzip sematic_server-0.0.1-py3-none-any.whl

# We use psycopg2_binary which comes compiled for the host platform
# We need to get it again for the container platform
RUN rm -rf psycopg2*
RUN python3 -m pip install psycopg2-binary


# ENTRYPOINT [ "python3" ]

EXPOSE 5002
CMD python3 -m sematic.api.server --env container --debug
