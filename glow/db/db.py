# Standard Library
from contextlib import contextmanager
import typing

# Third-party
import sqlalchemy
import sqlalchemy.orm

_db_instance = None


class DB(object):

    _engine = None
    _Session = None

    def __init__(self, url):
        self._engine = sqlalchemy.create_engine(url)
        self._Session = sqlalchemy.orm.sessionmaker(bind=self._engine)

    def get_engine(self) -> sqlalchemy.engine.Engine:
        return self._engine

    @contextmanager
    def get_session(self) -> typing.Generator[sqlalchemy.orm.Session]:
        session = self._Session()
        try:
            yield session
        finally:
            session.close()


def db() -> DB:
    global _db_instance
    if _db_instance is None:
        url = None  # cloud_settings().db_settings.url
        _db_instance = DB(url) if url else LocalDB()
    return _db_instance


class LocalDB(DB):

    LOCAL_DB_FILE = "~/.glow/db.sqlite3"

    def __init__(self):
        super().__init__(self.LOCAL_DB_FILE)
