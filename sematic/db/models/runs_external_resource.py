# Third-party
from sqlalchemy import Column, ForeignKey, types

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.mixins.json_encodable_mixin import JSONEncodableMixin


# Q: Why not make resource_id a field on run?
# A: Because a run may use more than one resource.
# Q: Why not make run_id a field on external_resource?
# A: Because in the future we may support sharing external resources across runs.
class RunExternalResource(Base, JSONEncodableMixin):
    """A DB record that a particular run is using a particular external resource.

    Attributes
    ----------
    resource_id:
        The id of the external resource being used by the run.
    run_id:
        The id of the run using the resource.
    """

    __tablename__ = "runs_external_resources"

    resource_id: str = Column(
        types.String(), ForeignKey("external_resources.id"), primary_key=True
    )
    run_id: str = Column(types.String(), ForeignKey("runs.id"), primary_key=True)

    def __repr__(self) -> str:
        key_value_strings = [
            f"{field}={getattr(self, field)}"
            for field in (
                "resource_id",
                "run_id",
            )
        ]
        fields = ", ".join(key_value_strings)
        return f"RunExternalResource({fields})"
