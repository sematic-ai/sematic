# Standard Library
import logging

# Sematic
from sematic.resolver import Resolver
from sematic.runners.silent_runner import SilentRunner


logger = logging.getLogger(__name__)


class SilentResolver(SilentRunner, Resolver):
    """A stub to help facilitate the transition from Resolver -> Runner"""

    def __init__(self, *args, **kwargs):
        logger.warning(
            "SilentResolver will soon be deprecated in favor of SilentRunner. "
            "Please migrate as soon as you are able."
        )
        super().__init__(*args, **kwargs)
