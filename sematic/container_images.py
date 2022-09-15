# Standard Library
import os
import pathlib

import __main__

CONTAINER_IMAGE_ENV_VAR = "SEMATIC_CONTAINER_IMAGE"


class MissingCloudImage(Exception):
    pass


def has_container_image() -> bool:
    """Indicates whether Sematic has a Docker image that can be used for cloud execution.

    Returns
    -------
    True if an image can be found, False otherwise.
    """
    try:
        get_image_uri()
        return True
    except MissingCloudImage:
        return False


def get_image_uri() -> str:
    """Get the URI of the docker image associated with this execution.

    Returns
    -------
    The URI of the image to be used in this execution.
    """
    if CONTAINER_IMAGE_ENV_VAR in os.environ:
        return os.environ[CONTAINER_IMAGE_ENV_VAR]

    file_path = "{}_push_at_build.uri".format(os.path.splitext(__main__.__file__)[0])
    if not pathlib.Path(file_path).exists():
        raise MissingCloudImage(
            "Sematic needs access to a docker image containing the source code before "
            "it can run in the cloud. If such an image exists, please set "
            f"the environment variable: {CONTAINER_IMAGE_ENV_VAR}."
        )
    with open(file_path) as f:
        return f.read()
