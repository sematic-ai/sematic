# Standard Library
import logging
import time
from dataclasses import dataclass, replace
from typing import Optional

# Sematic
from sematic.plugins.abstract_external_resource import (
    AbstractExternalResource,
    ResourceState,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TimedMessage(AbstractExternalResource):
    """A simple external resource to be used for demonstration purposes.

    The resource represents a message which can be accessed only for a limited
    period of time. It will begin deactivating either when an explicit call is
    made to deactivate it, or max_active_seconds have passed since the message
    became active.

    Attributes
    ----------
    epoch_time_activation_began:
        Time in epoch seconds that the resource began activating. 'None' if
        activation has not begun.
    epoch_time_deactivation_began:
        Time in epoch seconds that the resource began deactivating. 'None'
    allocation_seconds:
        The amount of time activation should take, in seconds.
    max_active_seconds:
        The maximum amount of time that the message will be readable, in seconds.
    message:
        The message to make available as long as the resource is active.
    """

    epoch_time_activation_began: Optional[float] = None
    epoch_time_deactivation_began: Optional[float] = None
    allocation_seconds: float = 1.0
    deallocation_seconds: float = 1.0
    max_active_seconds: float = 30.0
    message: str = ""

    def read_message(self) -> str:
        if self.status.state != ResourceState.ACTIVE:
            raise RuntimeError(
                f"Resource {self.id} is not active, but {self.status.state.value}"
            )
        if self._has_timed_out():
            raise RuntimeError(f"Resource {self.id} has timed out")
        return self.message

    def _has_timed_out(self) -> bool:
        if self.epoch_time_activation_began is None:
            return False
        now = time.time()
        time_since_activated = now - (
            self.epoch_time_activation_began + self.allocation_seconds
        )
        remaining_active_time = self.max_active_seconds - time_since_activated
        logger.info("Resource still active for %s s", remaining_active_time)
        return remaining_active_time < 0

    def _continue_transition(
        self,
        final_state: ResourceState,
        start_time: float,
        transition_duration: float,
        final_state_message: str,
    ) -> "TimedMessage":
        """Update the state while the resource is in a transitional state"""
        now = time.time()
        transition_time = now - start_time
        transition_time_remaining = transition_duration - transition_time
        if transition_time_remaining < 0:
            return replace(
                self,
                status=replace(
                    self.status,
                    state=final_state,
                    message=final_state_message,
                ),
            )
        else:
            message = (
                f"Resource is still {self.status.state.value}. "
                f"{transition_time_remaining}s remain."
            )
            logger.info(message)
            return replace(
                self,
                status=replace(
                    self.status,
                    state=self.status.state,
                    message=message,
                ),
            )

    def _do_activate(self, is_local: bool) -> "TimedMessage":
        logger.info(f"Activating {self.id}! is_local={is_local}")
        now = time.time()
        return replace(
            self,
            epoch_time_activation_began=now,
            status=replace(
                self.status,
                state=ResourceState.ACTIVATING,
                message=f"Allocating, should take {self.allocation_seconds}s to activate",
            ),
        )

    def _do_deactivate(self, status_message: Optional[str] = None) -> "TimedMessage":
        logger.info(f"Deactivating {self.id}")
        now = time.time()
        if status_message is None:
            status_message = (
                f"Dellocating, should take {self.deallocation_seconds}s to deactivate"
            )
        return replace(
            self,
            epoch_time_deactivation_began=now,
            status=replace(
                self.status,
                state=ResourceState.DEACTIVATING,
                message=status_message,
            ),
            message="",
        )

    def _do_update(self) -> "TimedMessage":
        logger.info(f"Updating state of {self.id}")
        if self.status.state == ResourceState.ACTIVATING:
            assert self.epoch_time_activation_began is not None  # satisfy mypy
            return self._continue_transition(
                final_state=ResourceState.ACTIVE,
                start_time=self.epoch_time_activation_began,
                transition_duration=self.allocation_seconds,
                final_state_message="Resource is ready to use",
            )
        elif self.status.state == ResourceState.DEACTIVATING:
            assert self.epoch_time_deactivation_began is not None  # satisfy mypy
            return self._continue_transition(
                final_state=ResourceState.DEACTIVATED,
                start_time=self.epoch_time_deactivation_began,
                transition_duration=self.deallocation_seconds,
                final_state_message="Resource has been deactivated.",
            )
        elif self.status.state == ResourceState.ACTIVE:
            if self._has_timed_out():
                return self._do_deactivate(status_message="Resource timed out.")

        return replace(
            self,
            status=replace(
                self.status,
                state=self.status.state,
                message="Nothing has changed...",
            ),
        )
