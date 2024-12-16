"""
Module defining the Resolution data model.

Note that this class is sometimes referred to as a "Pipeline Run."
It will be formally renamed to that with
https://github.com/sematic-ai/sematic/issues/959

Notes regarding container images
--------------------------------
In the case of cloud execution (using `CloudRunner`), the default behavior
uses a single container image for remote jobs (driver job + worker jobs). See
docs/multiple-base-images.md for the rationale behind this design choice.

As an undocumented behavior, Sematic supports different **base** images per
function. This works using a mapping of tag to base image specified by users in
the build information (`bases` argument to the `sematic_pipeline` Bazel target
at this time). Users then specify in the `sematic.func` decorator what base
image to use with the `base_image_tag` argument that should correspond to one of
the keys in the mapping passed to `sematic_pipeline`.
"""

# Standard Library
import dataclasses
import json
import logging
from enum import Enum, unique
from typing import Dict, FrozenSet, Optional, Union

# Third-party
from sqlalchemy import ForeignKey, types
from sqlalchemy.orm import Mapped, mapped_column, validates  # type: ignore

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.git_info import GitInfo
from sematic.db.models.mixins.has_organization_mixin import HasOrganizationMixin
from sematic.db.models.mixins.has_user_mixin import HasUserMixin
from sematic.db.models.mixins.json_encodable_mixin import (
    ENUM_KEY,
    JSON_KEY,
    REDACTED_KEY,
    JSONEncodableMixin,
)
from sematic.resolvers.resource_requirements import ResourceRequirements
from sematic.types.serialization import (
    value_from_json_encodable,
    value_to_json_encodable,
)


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

    CREATED = "CREATED"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    COMPLETE = "COMPLETE"
    CANCELED = "CANCELED"

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

    def is_terminal(self) -> bool:
        return len(_ALLOWED_TRANSITIONS[self]) == 0

    @classmethod
    def terminal_states(cls) -> FrozenSet:
        return _TERMINAL_STATES

    @classmethod
    def non_terminal_states(cls) -> FrozenSet:
        return _NON_TERMINAL_STATES


_ALLOWED_TRANSITIONS = {
    # Local resolver can jump straight to RUNNING
    None: {
        ResolutionStatus.CREATED,
        ResolutionStatus.SCHEDULED,
        ResolutionStatus.RUNNING,
        ResolutionStatus.FAILED,
        ResolutionStatus.CANCELED,
    },
    ResolutionStatus.CREATED: {
        ResolutionStatus.SCHEDULED,
        ResolutionStatus.FAILED,
        ResolutionStatus.CANCELED,
    },
    ResolutionStatus.SCHEDULED: {
        ResolutionStatus.RUNNING,
        ResolutionStatus.FAILED,
        ResolutionStatus.CANCELED,
    },
    ResolutionStatus.RUNNING: {
        ResolutionStatus.COMPLETE,
        ResolutionStatus.FAILED,
        ResolutionStatus.CANCELED,
    },
    ResolutionStatus.COMPLETE: {},
    ResolutionStatus.FAILED: {},
    ResolutionStatus.CANCELED: {},
}

_TERMINAL_STATES = frozenset({state for state in ResolutionStatus if state.is_terminal()})
_NON_TERMINAL_STATES = frozenset(
    {state for state in ResolutionStatus if not state.is_terminal()}
)


class InvalidResolution(Exception):
    pass


@unique
class ResolutionKind(Enum):
    """The kind of compute used to execute the resolution"""

    LOCAL = "LOCAL"  # for non-detached mode
    KUBERNETES = "KUBERNETES"  # for detached mode


class Resolution(Base, HasUserMixin, HasOrganizationMixin, JSONEncodableMixin):
    """Represents a session of a resolver.

    Attributes
    ----------
    root_id:
        The id of the root run which this resolution is resolving.
    status:
        The state of the resolver session, see ResolutionStatus.
    kind:
        The kind of resolver session (ex: on k8s or not).
    git_info:
        Information about the git remote, branch, commit, and dirty bit
        for the environment from which the resolution was submitted
    settings_env_vars:
        The Sematic settings from the user's environment for the user
        who launched this resolution. Removed from the API payload for
        obfuscation purposes.
    container_image_uri:
        The image URI used for the driver job.
    container_image_uris:
        A mapping of tag to base images to be used for runs in the graph
        based on the `base_image_tag` argument passed to the `sematic.func`
        decorator.
    client_version:
        The version of Sematic that is in use by the container that this
        resolution executes with.
    cache_namespace:
        The cache key namespace in which the executed funcs's outputs will
        be cached, as long as they also have the `cache` flag activated.
    user_id:
        User who submitted this resolution.
    organization_id:
        The organization under which this resolution was submitted.
    run_command:
        The CLI command used to launch this resolution, if applicable.
    build_config:
        The configuration used to build the pipeline container image, if applicable.
    resource_requirements_json:
        The resource requirements the runner pod should use.
    """

    __tablename__ = "resolutions"

    root_id: Mapped[str] = mapped_column(
        types.String(),
        ForeignKey("runs.id"),
        nullable=False,
        primary_key=True,
    )
    status: Mapped[ResolutionStatus] = mapped_column(  # type: ignore
        types.String(), nullable=False, info={ENUM_KEY: ResolutionStatus}
    )
    kind: Mapped[ResolutionKind] = mapped_column(  # type: ignore
        types.String(), nullable=False, info={ENUM_KEY: ResolutionKind}
    )
    git_info_json: Mapped[Optional[str]] = mapped_column(  # type: ignore
        types.JSON(), nullable=True, info={JSON_KEY: True}
    )
    # REDACTED_KEY: Scrub the environment variables before returning from the
    # API. They can contain sensitive info like API keys. On write,
    # we consider this field to be immutable, so we will just re-use
    # whatever was already in the DB for it
    settings_env_vars: Mapped[Dict[str, str]] = mapped_column(
        types.JSON(), nullable=False, default=lambda: {}, info={REDACTED_KEY: True}
    )

    container_image_uris: Mapped[Optional[Dict[str, str]]] = mapped_column(
        types.JSON(), nullable=True
    )
    container_image_uri: Mapped[Optional[str]] = mapped_column(
        types.String(), nullable=True
    )
    client_version: Mapped[Optional[str]] = mapped_column(types.String(), nullable=True)
    cache_namespace: Mapped[Optional[str]] = mapped_column(types.String(), nullable=True)
    run_command: Mapped[Optional[str]] = mapped_column(types.String(), nullable=True)
    build_config: Mapped[Optional[str]] = mapped_column(types.String(), nullable=True)
    resource_requirements_json: Mapped[Optional[str]] = mapped_column(
        types.JSON(), nullable=True
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
        if self.kind != ResolutionKind.LOCAL.value and self.container_image_uri is None:
            raise InvalidResolution(
                f"Non-local resolution {self.root_id} must have a docker URI"
            )
        if not ResolutionStatus.is_allowed_transition(None, self.status):
            raise InvalidResolution(
                f"New resolution {self.root_id} can't begin in the {self.status} state."
            )

    @property
    def git_info(self) -> Optional[GitInfo]:
        if self.git_info_json is None:
            return None

        json_encodable = json.loads(self.git_info_json)
        return GitInfo(**json_encodable)

    @git_info.setter
    def git_info(self, value: Optional[GitInfo]) -> None:
        if value is None:
            self.git_info_json = None
            return

        # git_info_json is not mutable; any update posted to api_client will be rejected
        # we therefore need to sort the keys
        # for the same reason, we can't use value_to_json_encodable, because it imposes
        # the values/types/root_type semantics
        self.git_info_json = json.dumps(dataclasses.asdict(value), sort_keys=True)

    @property
    def resource_requirements(self) -> Optional[ResourceRequirements]:
        if self.resource_requirements_json is None:
            return None

        json_encodable = json.loads(self.resource_requirements_json)
        return value_from_json_encodable(json_encodable, ResourceRequirements)

    @resource_requirements.setter
    def resource_requirements(self, value: Optional[ResourceRequirements]) -> None:
        if value is None:
            self.resource_requirements_json = None
            return
        self.resource_requirements_json = json.dumps(
            value_to_json_encodable(value, ResourceRequirements)
        )


# Aliases to aid in the rename of resolution -> pipeline run
# The current code takes the following convention with regards
# to which variant is used in what places:
# - Runner code uses the "pipeline run" variants
# - API client python method names use the "pipeline run" variants
# - API client HTTP paths use "resolution" API paths
# - Server-side API supports only "resolution" HTTP paths
# - DB queries module uses "resolution" name
# - DB tables use "resolution" name
#
# The plan is to progress down this list in order
# as changes are implemented. For the server-side API
# endpoints, there will be a transition period where
# both /api/v1/resolution and api/v1/pipeline_run
# variants will be accepted, to support backwards
# compatibility.
PipelineRunStatus = ResolutionStatus
InvalidPipelineRun = InvalidResolution
PipelineRunKind = ResolutionKind
PipelineRun = Resolution
