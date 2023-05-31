"""Test launch script that cooperates."""
# Standard Library
import os
import sys

# we expect it to run as the main script
if __name__ == "__main__":
    # we expect to have the SEMATIC_CONTAINER_IMAGE env var set, as that's what the
    # Runner uses to specify the K8 pod image
    image_uri = os.getenv("SEMATIC_CONTAINER_IMAGE")
    # we expect to be called with the name of a tmp file where to write the value of the
    # SEMATIC_CONTAINER_IMAGE env var
    tmp_file = sys.argv[1]

    # mypy picks up this file
    assert image_uri is not None

    with open(tmp_file, "wt") as f:
        f.write(image_uri)
