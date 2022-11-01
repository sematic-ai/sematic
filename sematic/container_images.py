# Standard Library
import os
import re
from typing import Dict

import __main__  # isort:skip

CONTAINER_IMAGE_ENV_VAR = "SEMATIC_CONTAINER_IMAGE"

DEFAULT_BASE_IMAGE_TAG = "default"


class MissingContainerImage(Exception):
    pass


def has_container_image() -> bool:
    """Indicates whether Sematic has a Docker image that can be used for cloud execution.

    Returns
    -------
    True if an image can be found, False otherwise.
    """
    try:
        get_image_uris()
        return True
    except MissingContainerImage:
        return False


def get_image_uris() -> Dict[str, str]:
    """Get the URI of the docker image associated with this execution.

    Returns
    -------
    The URI of the image to be used in this execution.
    """
    if CONTAINER_IMAGE_ENV_VAR in os.environ:
        return {DEFAULT_BASE_IMAGE_TAG: os.environ[CONTAINER_IMAGE_ENV_VAR]}

    tagged_uris_map = {}

    dir_path, file_name = os.path.split(__main__.__file__)

    image_file_regex = r"{}_(.*?)_push_at_build.uri".format(
        os.path.splitext(file_name)[0]
    )

    for file_path in os.listdir(dir_path):
        tag_matches = re.findall(image_file_regex, file_path)
        if len(tag_matches) == 1:
            tag = tag_matches[0]
            absolute_file_path = (
                f"{os.path.splitext(__main__.__file__)[0]}_{tag}_push_at_build.uri"
            )

            with open(absolute_file_path) as f:
                tagged_uris_map[tag] = f.read()

    if len(tagged_uris_map) == 0:
        raise MissingContainerImage(
            "Sematic needs access to a docker image containing the source code before "
            "it can run in the cloud. If such an image exists, please set "
            f"the environment variable: {CONTAINER_IMAGE_ENV_VAR}."
        )

    return tagged_uris_map
