# Third-party
import pytest

# Glow
import glow.db.db as db


@pytest.fixture(scope="function")
def test_db():
    original_db = db._db_instance
    temp_db = db.LocalDB("sqlite://")

    with open("glow/db/schema.sql", "r") as file:
        schema = file.read()

    connection = temp_db.get_engine().raw_connection()
    cursor = connection.cursor()
    cursor.executescript(schema)

    db._db_instance = temp_db

    try:
        yield temp_db
    finally:
        db._db_instance = original_db
