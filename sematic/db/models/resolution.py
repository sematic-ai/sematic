# Standard Library
import logging
from enum import Enum, unique
from typing import Dict, Optional, Union

# Third party
from sqlalchemy import Column, types
from sqlalchemy.orm import validates

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.json_encodable_mixin import ENUM_KEY, JSONEncodableMixin

logger = logging.getLogger(__name__)


@unique
class ResolutionStatus(Enum):
    """The status of the resolution itself.

    This is distinct from the status of the root run: the root run might not be running
    yet, but the resolution is. Or something may fail in the resolver itself, rather than
    in one of the runs involved in it.

    States
    ------
    SCHEDULED:
        K8s (or the local process, for non-detached) has been asked to execute the
        resolution, but the code has not started executing for it yet.
    RUNNING:
        The code for the resolution is executing.
    FAILED:
        There was an error in the resolution itself, NOT necessarily in the runs that it's
        managing. The resolution may have started getting too many 500s from the Sematic
        server, for example.
    COMPLETE:
        The resolution is done, and it will do no more work. This status may be used even
        if the root run failed, so long as it failed due to some issue in the Sematic
        func execution and not for some other reason. It may also be used if the root run
        was canceled, so long as the cancellation was exited cleanly.
    """

    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    COMPLETE = "COMPLETE"

    @classmethod
    def is_allowed_transition(
        cls,
        from_status: Optional[Union["ResolutionStatus", str]],
        to_status: Union["ResolutionStatus", str],
    ) -> bool:
        """Check whether it's valid to move from the from_status to the to_status

        Parameters
        ----------
        from_status:
            The status being moved from, or None if this is a new resolution.
        to_status:
            The status being moved to

        Returns
        -------
        True if the transition is valid, False otherwise
        """
        if from_status is not None and not isinstance(from_status, ResolutionStatus):
            from_status = ResolutionStatus[from_status]
        if not isinstance(to_status, ResolutionStatus):
            to_status = ResolutionStatus[to_status]
        return to_status in _ALLOWED_TRANSITIONS[from_status]


_ALLOWED_TRANSITIONS = {
    # Local resolver can jump straight to RUNNING
    None: {
        ResolutionStatus.SCHEDULED,
        ResolutionStatus.RUNNING,
        ResolutionStatus.FAILED,
    },
    ResolutionStatus.SCHEDULED: {ResolutionStatus.RUNNING, ResolutionStatus.FAILED},
    ResolutionStatus.RUNNING: {ResolutionStatus.COMPLETE, ResolutionStatus.FAILED},
    ResolutionStatus.COMPLETE: {},
    ResolutionStatus.FAILED: {},
}


class InvalidResolution(Exception):
    pass


@unique
class ResolutionKind(Enum):
    """The kind of compute used to execute the resolution"""

    LOCAL = "LOCAL"  # for non-detached mode
    KUBERNETES = "KUBERNETES"  # for detached mode


class Resolution(Base, JSONEncodableMixin):
    """Represents a session of a resolver

    Attributes
    ----------
    root_id:
        The id of the root run which this resolution is resolving.
    status:
        The state of the resolver session, see ResolutionStatus.
    kind:
        The kind of resolver session (ex: on k8s or not).
    docker_image_uri:
        The docker image URI for the resolution. May be null when
        doing a non-detached (local) resolution
    settings_env_vars:
        The Sematic settings from the user's environment for the user
        who launched this resolution.
    """

    __tablename__ = "resolutions"

    root_id: str = Column(
        types.String(),
        nullable=False,
        primary_key=True,
    )
    status: ResolutionStatus = Column(  # type: ignore
        types.String(), nullable=False, info={ENUM_KEY: ResolutionStatus}
    )
    kind: ResolutionKind = Column(  # type: ignore
        types.String(), nullable=False, info={ENUM_KEY: ResolutionKind}
    )
    docker_image_uri: Optional[str] = Column(
        types.String(), nullable=True, default=None
    )
    settings_env_vars: Dict[str, str] = Column(
        types.JSON, nullable=False, default=lambda: {}
    )

    @validates("status")
    def validate_status(self, key, value) -> str:
        """
        Validates that the status value is allowed.
        """
        if isinstance(value, ResolutionStatus):
            return value.value

        try:
            return ResolutionStatus[value].value
        except Exception:
            raise ValueError("status must be a ResolutionStatus, got {}".format(value))

    @validates("kind")
    def validate_kind(self, key, value) -> str:
        """
        Validates that the kind value is allowed.
        """
        if isinstance(value, ResolutionKind):
            return value.value

        try:
            return ResolutionKind[value].value
        except Exception:
            raise ValueError("kind must be a ResolutionKind, got {}".format(value))

    def update_with(self, other: "Resolution") -> None:
        """Use the other resolution to update this one.

        Parameters
        ----------
        other:
            The new resolution that is meant to update this one

        Raises
        ------
        InvalidResolution if the update is not valid.
        """
        mutable_fields = {"status"}
        for column in Resolution.__table__.columns:
            column_key: str = column.key  # type: ignore
            if column_key in mutable_fields:
                continue
            original_value = getattr(self, column_key)
            new_value = getattr(other, column_key)
            if original_value != new_value:
                raise InvalidResolution(
                    f"Cannot update {column_key} of resolution {self.root_id} after "
                    f"it has been created. Original value: '{original_value}', "
                    f"new value: '{new_value}' (will not be used)"
                )

        if other.status != self.status:
            if not ResolutionStatus.is_allowed_transition(self.status, other.status):
                raise InvalidResolution(
                    f"Resolution {self.root_id} cannot be moved from the {self.status} "
                    f"state to the {other.status} state."
                )
            logger.info(
                "Status of resolution %s changing from %s to %s",
                self.root_id,
                self.status,
                other.status,
            )

        for field in mutable_fields:
            setattr(self, field, getattr(other, field))

    def validate_new(self):
        """Confirm that the resolution is valid for a resolution that is just beginning.

        Raises
        ------
        InvalidResolution if the resolution is not valid.
        """
        if self.kind != ResolutionKind.LOCAL.value and self.docker_image_uri is None:
            raise InvalidResolution(
                f"Non-local resolution {self.root_id} must have a docker URI"
            )
        if not ResolutionStatus.is_allowed_transition(None, self.status):
            raise InvalidResolution(
                f"New resolution {self.root_id} can't begin in the {self.status} state."
            )
