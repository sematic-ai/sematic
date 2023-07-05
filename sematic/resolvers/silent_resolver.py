# Standard Library
import logging

# Sematic
from sematic.runners.silent_runner import SilentRunner

logger = logging.getLogger(__name__)


class SilentResolver(SilentRunner):
    # Stub to allow people time to transition to Runner instead
    def __init__(self, *args, **kwargs):
        logger.warning(
            "SilentResolver will soon be deprecated in favor of SilentRunner. "
            "Please migrate as soon as you are able."
        )
        return super().__init__(*args, **kwargs)
