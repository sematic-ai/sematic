"""
Module keeping the connection to the DB.
"""
# Standard Library
from contextlib import contextmanager
import typing

# Third-party
import sqlalchemy
import sqlalchemy.orm

# Glow
from glow.config import get_config


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
    from glow.db.db import db

    with db().get_session() as session:
        session.query(...)
    """
    global _db_instance
    if _db_instance is None:
        url: typing.Optional[str] = None  # cloud_settings().db_settings.url
        _db_instance = DB(url) if url is not None else LocalDB()
    return _db_instance


class LocalDB(DB):
    """
    Subclass of DB to represent a local SQLite DB.
    """

    LOCAL_DB_FILE = "sqlite:///{}/db.sqlite3".format(get_config().config_dir)

    def __init__(self, url: typing.Optional[str] = None):
        if url is None:
            url = self.LOCAL_DB_FILE
        super().__init__(url)
