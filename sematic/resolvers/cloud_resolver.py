# Standard Library
import logging

# Sematic
from sematic.resolver import Resolver
from sematic.runners.cloud_runner import CloudRunner


logger = logging.getLogger(__name__)


class CloudResolver(CloudRunner, Resolver):
    """A stub to help facilitate the transition from Resolver -> Runner"""

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        logger.warning(
            "CloudResolver will soon be deprecated in favor of CloudRunner. "
            "Please migrate as soon as you are able."
        )
        super().__init__(*args, **kwargs)
