# Standard library
from typing import Optional
import os

# Sematic
from sematic.config import get_config


def get_server_pid() -> Optional[int]:
    try:
        with open(get_config().server_pid_file_path, "rb") as file:
            return int(file.read())
    except FileNotFoundError:
        return None


def server_is_running() -> bool:
    server_pid = get_server_pid()

    if server_pid is None:
        return False

    try:
        os.kill(server_pid, 0)
        return True
    except OSError:
        return False
