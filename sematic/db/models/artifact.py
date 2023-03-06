# Standard Library
import datetime

# Third-party
from sqlalchemy import Column, types

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.mixins.json_encodable_mixin import JSON_KEY, JSONEncodableMixin


class Artifact(Base, JSONEncodableMixin):
    # we use content-addressed values for artifacts, with the id being
    # generated from the type and value themselves
    # when a resolution generates an artifact which has been seen before and which is
    # present in the db, only the updated_at field is actually updated
    # if you need to add new fields, these probably need to be handled in an appropriate
    # manner in the location where artifacts are saved to the db, which at the time of
    # writing is `sematic.db.queries.py`

    __tablename__ = "artifacts"

    id: str = Column(types.String(), primary_key=True)
    json_summary: str = Column(types.JSON(), nullable=False, info={JSON_KEY: True})
    type_serialization: str = Column(
        types.JSON(), nullable=False, info={JSON_KEY: True}
    )
    created_at: datetime.datetime = Column(
        types.DateTime(), nullable=False, default=datetime.datetime.utcnow
    )
    updated_at: datetime.datetime = Column(
        types.DateTime(),
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    def assert_matches(self, other: "Artifact") -> None:
        """Ensure the content of this artifact matches the content of the other.

        Ignore timestamp fields, as these do not represent differences in the
        artifact itself (but rather metadata about it).

        Parameters
        ----------
        other:
            The artifact to compare against.
        """
        ignore_fields = {"created_at", "updated_at"}

        for column in Artifact.__table__.columns:
            if column.key in ignore_fields:
                continue
            if column.key is None:
                continue
            current_val = getattr(self, column.key)
            other_val = getattr(other, column.key)
            if current_val != other_val:
                raise ValueError(
                    f"Artifact content change detected for field '{column.key}': "
                    f" original: '{current_val}' new: '{other_val}'"
                )
