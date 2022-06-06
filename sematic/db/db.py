"""
Module keeping the connection to the DB.
"""
# Standard Library
from contextlib import contextmanager
import typing

# Third-party
import sqlalchemy
import sqlalchemy.orm

# Sematic
from sematic.config import get_config


class DB:
    """
    Base class to describe SQLAlchemy database
    connections.
    """

    def __init__(self, url: str):
        self._engine = sqlalchemy.create_engine(url)
        self._Session = sqlalchemy.orm.sessionmaker(bind=self._engine)

    def get_engine(self) -> sqlalchemy.engine.Engine:
        return self._engine

    @contextmanager
    def get_session(self) -> typing.Generator[sqlalchemy.orm.Session, None, None]:
        session = self._Session()
        try:
            yield session
        finally:
            session.close()


_db_instance: typing.Optional[DB] = None


def db() -> DB:
    """
    Convenience method to access the current database
    connection.

    This should be the primary way any code accesses the DB.

    Example
    -------
    from sematic.db.db import db

    with db().get_session() as session:
        session.query(...)
    """
    global _db_instance
    if _db_instance is None:
        url = get_config().db_url
        _db_instance = DB(url)
    return _db_instance
