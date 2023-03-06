# Standard Library
import uuid

# Third-party
from sqlalchemy.sql import text

# Sematic
from sematic.db.db import db


def up():
    with db().get_engine().begin() as conn:
        users = conn.execute(
            "SELECT "
            "email, first_name, last_name, avatar_url, api_key, created_at, updated_at "
            "FROM users;"
        )

        for user in users:
            conn.execute(
                text(
                    "INSERT INTO users_tmp ("
                    "id, email, first_name, last_name, avatar_url, "
                    "api_key, created_at, updated_at"
                    ") VALUES ("
                    ":id, :email, :first_name, :last_name, :avatar_url, "
                    ":api_key, :created_at, :updated_at"
                    ");"
                ),
                dict(
                    id=uuid.uuid4().hex,
                    email=user[0],
                    first_name=user[1],
                    last_name=user[2],
                    avatar_url=user[3],
                    api_key=user[4],
                    created_at=user[5],
                    updated_at=user[6],
                ),
            )


def down():
    with db().get_engine().begin() as conn:
        conn.execute(
            "INSERT INTO users "
            "(email, first_name, last_name, avatar_url, api_key, created_at, updated_at) "
            "SELECT "
            "email, first_name, last_name, avatar_url, api_key, created_at, updated_at "
            "FROM users_tmp;"
        )
