# Standard Library
import logging
import os
import shutil

# Sematic
from sematic.config.config import get_config


logger = logging.getLogger(__name__)

SQLITE_SCHEMA = "sqlite://"


def back_up_db_file(suffix: str) -> None:
    try:
        url = get_config().db_url
        if not url.startswith(SQLITE_SCHEMA):
            raise ValueError(
                f"Unable to locate Sqlite database file based on configuration: {url}"
            )

        schema_length = len(SQLITE_SCHEMA)
        db_file_path = url[schema_length:]
        if not os.path.exists(db_file_path):
            raise ValueError(f"Sqlite database file {db_file_path} does not exist")

        backup_file_path = f"{db_file_path}_{suffix}.bck"

        if os.path.exists(backup_file_path):
            os.remove(backup_file_path)

        shutil.copyfile(db_file_path, backup_file_path)

    except BaseException as e:
        logger.exception("Unable to back up Sqlite database file: %s", str(e))


def reinstate_db_file_from_backup(suffix: str) -> None:
    try:
        url = get_config().db_url
        if not url.startswith(SQLITE_SCHEMA):
            raise ValueError(
                f"Unable to locate Sqlite database file based on configuration: {url}"
            )

        schema_length = len(SQLITE_SCHEMA)
        db_file_path = url[schema_length:]
        backup_file_path = f"{db_file_path}_{suffix}.bck"

        if not os.path.exists(backup_file_path):
            raise ValueError(
                f"Sqlite database backup file {backup_file_path} does not exist"
            )
        if os.path.getsize(backup_file_path) == 0:
            raise ValueError(f"Sqlite database backup file {backup_file_path} is empty")

        if os.path.exists(db_file_path):
            down_backup_file_path = f"{db_file_path}.down.bck"
            shutil.copyfile(db_file_path, down_backup_file_path)
            os.remove(db_file_path)

        shutil.copyfile(backup_file_path, db_file_path)

    except BaseException as e:
        logger.exception("Unable to reinstate Sqlite database backup file: %s", str(e))
