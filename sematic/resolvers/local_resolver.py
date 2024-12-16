# Standard Library
import logging

# Sematic
from sematic.resolver import Resolver
from sematic.runners.local_runner import LocalRunner


logger = logging.getLogger(__name__)


class LocalResolver(LocalRunner, Resolver):
    """A stub to help facilitate the transition from Resolver -> Runner"""

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        logger.warning(
            "LocalResolver will soon be deprecated in favor of LocalRunner. "
            "Please migrate as soon as you are able."
        )
        super().__init__(*args, **kwargs)
