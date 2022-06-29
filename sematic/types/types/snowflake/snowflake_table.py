# Standard library
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator

# Third-party
import pandas
import snowflake.connector

# Sematic
from sematic.credentials import get_credential, CredentialKeys


@dataclass
class SnowflakeTable:
    """
    A class to easily access Snowflake tables.
    """

    database: str
    table: str

    def _connection(self) -> snowflake.connector.connection.SnowflakeConnection:
        return snowflake.connector.connect(
            user=get_credential(CredentialKeys.snowflake, "SNOWFLAKE_USER"),
            password=get_credential(CredentialKeys.snowflake, "SNOWFLAKE_PASSWORD"),
            account=get_credential(CredentialKeys.snowflake, "SNOWFLAKE_ACCOUNT"),
            database=self.database,
        )

    @contextmanager
    def _cursor(
        self,
    ) -> Generator[snowflake.connector.cursor.SnowflakeCursor, None, None]:
        with self._connection() as ctx:
            yield ctx.cursor()

    def to_df(self, limit: int = -1) -> pandas.DataFrame:
        """
        Output content of the table to a `pandas.DataFrame`.

        Parameters
        ----------
        limit: Optional[int]
            Maximum number of rows to return. Defaults to -1, i.e. all.
        """
        with self._cursor() as cursor:
            cursor.execute("SELECT * FROM {} LIMIT {};".format(self.table, limit))
            return cursor.fetch_pandas_all()
