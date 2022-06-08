# Standard library
from typing import Optional, Union
import subprocess
import os

# Sematic
from sematic.config import get_config


def server_is_running():
    return get_server_pid() is not None


def write_server_pid(pid: Union[int, str]):
    with open(_get_server_pid_file_path(), "w") as pid_file:
        pid_file.write(str(pid))


def get_server_pid() -> Optional[str]:
    pid = None
    try:
        with open(_get_server_pid_file_path(), "r") as pid_file:
            pid = pid_file.read()
    except FileNotFoundError:
        pass

    if pid is not None and len(pid) > 0:
        command = "ps | grep {} | grep -v grep".format(pid)
        process = subprocess.run(command, shell=True, capture_output=True)

        if process.returncode == 0 and len(process.stdout.decode()) > 0:
            return pid

    # Attempt to find server with ps
    # Using multiple greps because we may be running installed (sematic.api.server) or
    # In a Bazel env (sematic/api/server.py)
    command = "ps | grep sematic | grep api | grep server | grep -v grep"
    process = subprocess.run(
        command,
        shell=True,
        capture_output=True,
    )

    output = process.stdout.decode()
    if len(output) > 0:
        pid = output.split(" ")[0]
        write_server_pid(pid)

    return None


def _get_server_pid_file_path() -> str:
    return os.path.join(get_config().config_dir, "server.pid")
