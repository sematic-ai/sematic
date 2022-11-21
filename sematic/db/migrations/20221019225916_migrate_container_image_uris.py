# Standard Library
import json

# Third-party
from sqlalchemy.sql import text

# Sematic
from sematic.db.db import db


def up():
    with db().get_engine().begin() as conn:
        resolution_id_container_image_uri_pairs = conn.execute(
            "SELECT root_id, container_image_uri "
            "FROM resolutions "
            "WHERE container_image_uris IS NULL "
            "AND container_image_uri IS NOT NULL"
        )

        for (
            resolution_id,
            container_image_uri,
        ) in resolution_id_container_image_uri_pairs:
            container_image_uris = json.dumps({"default": container_image_uri})

            conn.execute(
                text(
                    "UPDATE resolutions "
                    "SET container_image_uris = :container_image_uris "
                    "WHERE root_id = :root_id"
                ),
                dict(
                    container_image_uris=container_image_uris,
                    root_id=resolution_id,
                ),
            )


def down():
    pass
