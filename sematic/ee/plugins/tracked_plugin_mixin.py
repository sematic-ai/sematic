# Standard Library
import logging

# Third-party
import posthog  # type: ignore

# Sematic
from sematic.db.models.user import User

logger = logging.getLogger(__name__)


class TrackedPluginMixin:
    """
    A mixin for basic usage tracking of EE plug-ins.
    """

    @classmethod
    def track_usage(cls, **kwargs) -> None:
        """
        Register a tracking event.
        """
        user_id = None
        if "user" in kwargs:
            user: User = kwargs["user"]
            user_id = user.email

        event = kwargs.get("event", "used")

        posthog.project_api_key = "phc_zwWXIEnEuZNj9JxC870IrxocjcuxG5ZjNoaNdW8YgXF"

        try:
            posthog.capture(user_id, event=f"{cls.__name__} {event}")
        except Exception as e:
            logger.exception("Unable to track usage of %s: %s", cls.__name__, str(e))
