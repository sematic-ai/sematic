# Standard Library
from unittest.mock import patch

# Third-party
import pandas
import pytest

# Sematic
from sematic.types.types.snowflake.snowflake_table import SnowflakeTable


@pytest.fixture
def credentials():
    with patch(
        "sematic.types.types.snowflake.snowflake_table.get_user_setting",
        return_value="dummy",
    ):
        yield


@pytest.fixture
def snowflake_connector():
    with patch("snowflake.connector.connection.SnowflakeConnection._authenticate"):
        with patch("snowflake.connector.cursor.SnowflakeCursor.execute") as execute:
            yield execute


@patch(
    "snowflake.connector.cursor.SnowflakeCursor.fetch_pandas_all",
    return_value=pandas.DataFrame(dict(a=[1, 2])),
)
def test_snowflake_table(_, snowflake_connector, credentials):
    table = SnowflakeTable(database="STARBUCKS_PLACES_SAMPLE", table="CORE_POI")

    df = table.to_df(limit=10)

    assert len(df) == 2
