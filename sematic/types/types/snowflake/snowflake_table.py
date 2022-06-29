# Standard library
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator
import os

# Third-party
try:
    import pandas
    import pyarrow  # type: ignore  # noqa: F401
    import snowflake.connector
except ImportError as e:
    print(
        "You are attempting to use SnowflakeTable which requires the following dependencies:"  # noqa: E501
    )

    requirements_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "requirements.txt"
    )

    with open(requirements_path) as f:
        for line in f.read().split("\n"):
            print("\t{}".format(line))
        print()

    print("Install them with\n")
    print("\tpip3 install -r {}".format(requirements_path))
    raise e

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
