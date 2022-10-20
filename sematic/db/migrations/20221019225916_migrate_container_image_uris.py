# Third-party
import sqlalchemy

# Sematic
from sematic.container_images import DEFAULT_BASE_IMAGE_TAG
from sematic.db.db import db
from sematic.db.models.resolution import Resolution


def up():
    with db().get_session() as session:
        resolutions = (
            session.query(Resolution)
            .filter(
                sqlalchemy.and_(
                    Resolution.container_image_uris.is_(None),
                    Resolution.container_image_uri.is_not(None),
                )
            )
            .all()
        )

        for resolution in resolutions:
            resolution.container_image_uris = {
                DEFAULT_BASE_IMAGE_TAG: resolution.container_image_uri
            }

        session.add_all(resolutions)
        session.commit()


def down():
    pass
