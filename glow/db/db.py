# Standard Library
from contextlib import contextmanager
import typing

# Third-party
import sqlalchemy
import sqlalchemy.orm

# Glow
from glow.utils.config_dir import get_config_dir


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
    def get_session(self) -> typing.Generator[sqlalchemy.orm.Session, None, None]:
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

    LOCAL_DB_FILE = "sqlite:///{}/db.sqlite3".format(get_config_dir())

    def __init__(self, url: str = None):
        if url is None:
            url = self.LOCAL_DB_FILE
        super().__init__(url)
