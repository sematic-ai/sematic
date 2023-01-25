# Standard Library
import os
from typing import Dict


CONTAINER_IMAGE_ENV_VAR = "SEMATIC_CONTAINER_IMAGE"
CONTAINER_IMAGE_URIS_ENV_VAR = "SEMATIC_CONTAINER_IMAGE_URIS"

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

    if CONTAINER_IMAGE_URIS_ENV_VAR in os.environ:
        logger.debug("Reading container image mappings from environment: %s='%s'", CONTAINER_IMAGE_URIS_ENV_VAR, os.environ[CONTAINER_IMAGE_URIS_ENV_VAR])
        image_uris = os.environ[CONTAINER_IMAGE_URIS_ENV_VAR].split('::')

        for image_uri in image_uris:
            if not image_uri:
                continue
            tag, uri = image_uri.split('##')
            tagged_uris_map[tag] = uri

    if len(tagged_uris_map) == 0:
        raise MissingContainerImage(
            "Sematic needs access to a docker image containing the source code before "
            "it can run in the cloud. If such an image exists, please set "
            f"the environment variable: {CONTAINER_IMAGE_ENV_VAR}."
        )

    return tagged_uris_map
